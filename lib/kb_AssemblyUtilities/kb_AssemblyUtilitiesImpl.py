# -*- coding: utf-8 -*-
#BEGIN_HEADER
from __future__ import print_function
from __future__ import division

import logging
import os
import sys
import shutil
import hashlib
import subprocess
import requests
import re
import traceback
import uuid
from datetime import datetime
from pprint import pprint, pformat

from installed_clients.WorkspaceClient import Workspace
from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.AssemblyUtilClient import AssemblyUtil
from installed_clients.GenomeFileUtilClient import GenomeFileUtil
from installed_clients.MetagenomeUtilsClient import MetagenomeUtils
from installed_clients.SetAPIServiceClient import SetAPI
from installed_clients.KBaseReportClient import KBaseReport
#END_HEADER


class kb_AssemblyUtilities:
    '''
    Module Name:
    kb_AssemblyUtilities

    Module Description:
    A KBase module: kb_AssemblyUtilities
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "1.0.0"
    GIT_URL = "https://github.com/dcchivian/kb_AssemblyUtilities"
    GIT_COMMIT_HASH = "23e4960c7eb8b5760df434575ef1eb0a36b4118a"

    #BEGIN_CLASS_HEADER
    workspaceURL     = None
    shockURL         = None
    handleURL        = None
    serviceWizardURL = None
    callbackURL      = None
    scratch          = None

    # log
    def log(self, target, message):
        timestamp = str(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
        if target is not None:
            target.append('['+timestamp+'] '+message)
        print('['+timestamp+'] '+message)
        sys.stdout.flush()
    
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.shared_folder = config['scratch']
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)

        self.workspaceURL = config['workspace-url']
        self.shockURL = config['shock-url']
        self.handleURL = config['handle-service-url']
        self.serviceWizardURL = config['srv-wiz-url']
        self.callbackURL = os.environ['SDK_CALLBACK_URL']
        self.scratch = os.path.abspath(config['scratch'])

        pprint(config)

        if not os.path.exists(self.scratch):
            os.makedirs(self.scratch)
        #END_CONSTRUCTOR
        pass


    def run_filter_contigs_by_length(self, ctx, params):
        """
        :param params: instance of type "Filter_Contigs_by_Length_Params"
           (filter_contigs_by_length() ** **  Remove Contigs that are under a
           minimum threshold) -> structure: parameter "workspace_name" of
           type "workspace_name" (** The workspace object refs are of form:
           ** **    objects = ws.get_objects([{'ref':
           params['workspace_id']+'/'+params['obj_name']}]) ** ** "ref" means
           the entire name combining the workspace id and the object name **
           "id" is a numerical identifier of the workspace or object, and
           should just be used for workspace ** "name" is a string identifier
           of a workspace or object.  This is received from Narrative.),
           parameter "input_assembly_refs" of type "data_obj_ref", parameter
           "min_contig_length" of Long, parameter "output_name" of type
           "data_obj_name"
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: returnVal
        #BEGIN run_filter_contigs_by_length

        # very strange, re import from above isn't being retained in this scope
        import re

        #### Step 0: basic init
        ##
        console = []
        invalid_msgs = []
        report_text = ''
        self.log(console, 'Running run_filter_contigs_by_length(): ')
        self.log(console, "\n"+pformat(params))

        # Auth
        token = ctx['token']
        headers = {'Authorization': 'OAuth '+token}
        env = os.environ.copy()
        env['KB_AUTH_TOKEN'] = token

        # API Clients
        #SERVICE_VER = 'dev'  # DEBUG
        SERVICE_VER = 'release'
        # wsClient
        try:
            wsClient = Workspace(self.workspaceURL, token=token)
        except Exception as e:
            raise ValueError('Unable to instantiate wsClient with workspaceURL: '+ self.workspaceURL +' ERROR: ' + str(e))
        # setAPI_Client
        try:
            #setAPI_Client = SetAPI (url=self.callbackURL, token=ctx['token'])  # for SDK local.  local doesn't work for SetAPI
            setAPI_Client = SetAPI (url=self.serviceWizardURL, token=ctx['token'])  # for dynamic service
        except Exception as e:
            raise ValueError('Unable to instantiate setAPI_Client with serviceWizardURL: '+ self.serviceWizardURL +' ERROR: ' + str(e))
        # auClient
        try:
            auClient = AssemblyUtil(self.callbackURL, token=ctx['token'], service_ver=SERVICE_VER)
        except Exception as e:
            raise ValueError('Unable to instantiate auClient with callbackURL: '+ self.callbackURL +' ERROR: ' + str(e))
        # dfuClient
        try:
            dfuClient = DataFileUtil(self.callbackURL)
        except Exception as e:
            raise ValueError('Unable to instantiate dfu_Client with callbackURL: '+ self.callbackURL +' ERROR: ' + str(e))

        # param checks
        required_params = ['workspace_name',
                           'input_assembly_refs',
                           'min_contig_length',
                           'output_name'
                          ]
        for arg in required_params:
            if arg not in params or params[arg] == None or params[arg] == '':
                raise ValueError ("Must define required param: '"+arg+"'")

        # load provenance
        provenance = [{}]
        if 'provenance' in ctx:
            provenance = ctx['provenance']
        provenance[0]['input_ws_objects']=[]
        for input_ref in params['input_assembly_refs']:
            provenance[0]['input_ws_objects'].append(input_ref)

        # set the output paths
        timestamp = int((datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds()*1000)
        output_dir = os.path.join(self.scratch,'output.'+str(timestamp))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        html_output_dir = os.path.join(output_dir,'html')
        if not os.path.exists(html_output_dir):
            os.makedirs(html_output_dir)


        #### STEP 1: get assembly refs
        ##
        if len(invalid_msgs) == 0:
            set_obj_type = "KBaseSets.AssemblySet"
            assembly_obj_types = ["KBaseGenomeAnnotations.Assembly", "KBaseGenomes.ContigSet"]
            accepted_input_types = [set_obj_type] + assembly_obj_types
            assembly_refs = []
            assembly_names = []
            assembly_refs_seen = dict()
        
            for i,input_ref in enumerate(params['input_assembly_refs']):

                # assembly obj info
                try:
                    [OBJID_I, NAME_I, TYPE_I, SAVE_DATE_I, VERSION_I, SAVED_BY_I, WSID_I, WORKSPACE_I, CHSUM_I, SIZE_I, META_I] = range(11)  # object_info tuple
                    input_obj_info = wsClient.get_object_info_new ({'objects':[{'ref':input_ref}]})[0]
                    #print ("INPUT_OBJ_INFO")
                    #pprint(input_obj_info)  # DEBUG
                    input_obj_type = re.sub ('-[0-9]+\.[0-9]+$', "", input_obj_info[TYPE_I])  # remove trailing version
                    input_obj_name = input_obj_info[NAME_I]
                    self.log (console, "Adding ASSEMBLY: "+str(input_ref)+" "+str(input_obj_name))  # DEBUG
                except Exception as e:
                    raise ValueError('Unable to get object from workspace: (' + input_ref +'): ' + str(e))

                if input_obj_type not in accepted_input_types:
                    raise ValueError ("Input object of type '"+input_obj_type+"' not accepted.  Must be one of "+", ".join(accepted_input_types))

                # add members to assembly_ref list
                if input_obj_type in assembly_obj_types:
                    try:
                        assembly_seen = assembly_refs_seen[input_ref]
                        continue
                    except:
                        assembly_refs_seen[input_ref] = True
                        assembly_refs.append(input_ref)
                        assembly_names.append(input_obj_name)
                elif input_obj_type != set_obj_type:
                    raise ValueError ("bad obj type for input_ref: "+input_ref)
                else:  # add assembly set members

                    try:
                        assemblySet_obj = setAPI_Client.get_assembly_set_v1 ({'ref':input_ref, 'include_item_info':1})
                    except Exception as e:
                        raise ValueError('Unable to get object from workspace: (' + input_ref +')' + str(e))
                    
                    for assembly_obj in assemblySet_obj['data']['items']:
                        this_assembly_ref = assembly_obj['ref']
                        try:
                            assembly_seen = assembly_refs_seen[this_assembly_ref]
                            continue
                        except:
                            assembly_refs_seen[this_assembly_ref] = True
                            assembly_refs.append(this_assembly_ref)
                            try:
                                [OBJID_I, NAME_I, TYPE_I, SAVE_DATE_I, VERSION_I, SAVED_BY_I, WSID_I, WORKSPACE_I, CHSUM_I, SIZE_I, META_I] = range(11)  # object_info tuple
                                this_input_obj_info = wsClient.get_object_info_new ({'objects':[{'ref':this_assembly_ref}]})[0]
                                this_input_obj_type = re.sub ('-[0-9]+\.[0-9]+$', "", input_obj_info[TYPE_I])  # remove trailing version
                                this_input_obj_name = this_input_obj_info[NAME_I]
                                assembly_names.append(this_input_obj_name)
                            except Exception as e:
                                raise ValueError('Unable to get object from workspace: (' + this_assembly_ref +')' + str(e))


        #### STEP 2: Get assemblies to score as fasta files
        ##
        if len(invalid_msgs) == 0:
            self.log (console, "Retrieving Assemblies")  # DEBUG

            #assembly_outdir = os.path.join (output_dir, 'score_assembly')
            #if not os.path.exists(assembly_outdir):
            #    os.makedirs(assembly_outdir)
            score_assembly_file_paths = []

            for ass_i,input_ref in enumerate(assembly_refs):
                self.log (console, "\tAssembly: "+assembly_names[ass_i]+" ("+assembly_refs[ass_i]+")")  # DEBUG
                contig_file = auClient.get_assembly_as_fasta({'ref':assembly_refs[ass_i]}).get('path')
                sys.stdout.flush()
                contig_file_path = dfuClient.unpack_file({'file_path': contig_file})['file_path']
                score_assembly_file_paths.append(contig_file_path)
                #clean_ass_ref = assembly_ref.replace('/','_')
                #assembly_outfile_path = os.join(assembly_outdir, clean_assembly_ref+".fna")
                #shutil.move(contig_file_path, assembly_outfile_path)


        #### STEP 3: Get contig attributes and create filtered output files
        ##
        if len(invalid_msgs) == 0:
            filtered_contig_file_paths = []
            original_contig_count = []
            filtered_contig_count = []

            # score fasta lens in contig files
            read_buf_size  = 65536
            write_buf_size = 65536

            lens = []
            for ass_i,assembly_file_path in enumerate(score_assembly_file_paths):
                ass_name = assembly_names[ass_i]
                self.log (console, "Reading contig lengths in assembly: "+ass_name)  # DEBUG

                original_contig_count.append(0)
                filtered_contig_count.append(0)
                filtered_file_path = assembly_file_path+".min_contig_length="+str(params['min_contig_length'])+"bp"
                filtered_contig_file_paths.append(filtered_file_path)
                with open (assembly_file_path, 'r', read_buf_size) as ass_handle, \
                     open (filtered_file_path, 'w', write_buf_size) as filt_handle:
                    seq_buf = ''
                    last_header = ''
                    for fasta_line in ass_handle:
                        if fasta_line.startswith('>'):
                            if seq_buf != '':
                                original_contig_count[ass_i] += 1
                                seq_len = len(seq_buf)
                                if seq_len >= int(params['min_contig_length']):
                                    filtered_contig_count[ass_i] += 1
                                    filt_handle.write(last_header)  # last_header already has newline
                                    filt_handle.write(seq_buf+"\n")
                                seq_buf = ''
                                last_header = fasta_line
                        else:
                            seq_buf += ''.join(fasta_line.split())
                    if seq_buf != '':
                        original_contig_count[ass_i] += 1
                        seq_len = len(seq_buf)
                        if seq_len >= int(params['min_contig_length']):
                            filtered_contig_count[ass_i] += 1
                            filt_handle.write(last_header)  # last_header already has newline
                            filt_handle.write(seq_buf+"\n")
                        seq_buf = ''

                # DEBUG
                #with open (filtered_file_path, 'r', read_buf_size) as ass_handle:
                #    for fasta_line in ass_handle:
                #        print ("FILTERED LINE: '"+fasta_line+"'")


        #### STEP 4: save the filtered assemblies
        ##
        if len(invalid_msgs) == 0:
            non_zero_output_seen = False
            filtered_contig_refs  = []
            filtered_contig_names = []
            #assemblyUtil = AssemblyUtil(self.callbackURL)
            for ass_i,filtered_contig_file in enumerate(filtered_contig_file_paths):
                if filtered_contig_count[ass_i] == 0:
                    self.log (console, "SKIPPING totally filtered assembled contigs from "+assembly_names[ass_i])
                    filtered_contig_refs.append(None)
                    filtered_contig_names.append(None)
                else:
                    non_zero_output_seen = True
                    if len(assembly_refs) == 1:
                        output_obj_name = params['output_name']
                    else:
                        output_obj_name = assembly_names[ass_i]+".min_contig_length"+str(params['min_contig_length'])+"bp"
                    output_data_ref = auClient.save_assembly_from_fasta({
                        'file': {'path': filtered_contig_file},
                        'workspace_name': params['workspace_name'],
                        'assembly_name': output_obj_name
                    })
                    filtered_contig_refs.append(output_data_ref)
                    filtered_contig_names.append(output_obj_name)
            # save AssemblySet
            if len(assembly_refs) > 1 and non_zero_output_seen:
                items = []
                for ass_i,filtered_contig_file in enumerate(filtered_contig_file_paths):
                    if filtered_contig_count[ass_i] == 0:
                        continue
                    self.log (console, "adding filtered assembly: "+filtered_contig_names[ass_i])
                    items.append({'ref': filtered_contig_refs[ass_i],
                                  'label': filtered_contig_names[ass_i],
                                  #'data_attachment': ,                         
                                  #'info'                                       
                              })

                # load the method provenance from the context object                 
                self.log(console,"SETTING PROVENANCE")  # DEBUG                      
                provenance = [{}]
                if 'provenance' in ctx:
                    provenance = ctx['provenance']
                # add additional info to provenance here, in this case the input data object reference                                                           
                provenance[0]['input_ws_objects'] = []
                for assRef in params['input_assembly_refs']:
                    provenance[0]['input_ws_objects'].append(assRef)
                provenance[0]['service'] = 'kb_assembly_compare'
                provenance[0]['method'] = 'run_filter_contigs_by_length'

                # save AssemblySet
                self.log(console,"SAVING ASSEMBLY_SET")  # DEBUG
                output_assemblySet_obj = { 'description': params['output_name']+" filtered by min_contig_length >= "+str(params['min_contig_length'])+"bp",
                                           'items': items
                                       }
                output_assemblySet_name = params['output_name']
                try:
                    output_assemblySet_ref = setAPI_Client.save_assembly_set_v1 ({'workspace_name': params['workspace_name'],
                                                                                  'output_object_name': output_assemblySet_name,
                                                                                  'data': output_assemblySet_obj
                                                                              })['set_ref']
                except Exception as e:
                    raise ValueError('SetAPI FAILURE: Unable to save assembly set object to workspace: (' + params['workspace_name']+")\n" + str(e))


        #### STEP 5: generate and save the report
        ##
        if len(invalid_msgs) > 0:
            report_text += "\n".join(invalid_msgs)
            objects_created = None
        else:
            # report text
            if len(assembly_refs) > 1 and non_zero_output_seen:
                report_text += 'AssemblySet saved to: ' + params['workspace_name'] + '/' + params['output_name'] + "\n\n"
            for ass_i,filtered_contig_file in enumerate(filtered_contig_file_paths):
                report_text += 'ORIGINAL Contig count: '+str(original_contig_count[ass_i])+"\t"+'in Assembly '+assembly_names[ass_i]+"\n"
                report_text += 'FILTERED Contig count: '+str(filtered_contig_count[ass_i])+"\t"+'in Assembly '+filtered_contig_names[ass_i]+"\n\n"
                if filtered_contig_count[ass_i] == 0:
                    report_text += "  (no output object created for "+filtered_contig_names[ass_i]+")"+"\n"

            # created objects
            objects_created = None
            if non_zero_output_seen:
                objects_created = []
                if len(assembly_refs) > 1:
                    objects_created.append({'ref': output_assemblySet_ref, 'description': params['output_name']+" filtered min_contig_length >= "+str(params['min_contig_length'])+"bp"})
                for ass_i,filtered_contig_ref in enumerate(filtered_contig_refs):
                    if filtered_contig_count[ass_i] == 0:
                        continue
                    objects_created.append({'ref': filtered_contig_refs[ass_i], 'description': filtered_contig_names[ass_i]+" filtered min_contig_length >= "+str(params['min_contig_length'])+"bp"})

        # Save report
        print('Saving report')
        kbr = KBaseReport(self.callbackURL)
        try:
            report_info = kbr.create_extended_report(
                {'message': report_text,
                 'objects_created': objects_created,
                 'direct_html_link_index': 0,
                 'html_links': [],
                 'file_links': [],
                 'report_object_name': 'kb_filter_contigs_by_length_report_' + str(uuid.uuid4()),
                 'workspace_name': params['workspace_name']
                 })
        #except _RepError as re:
        except Exception as re:
            # not really any way to test this, all inputs have been checked earlier and should be
            # ok 
            print('Logging exception from creating report object')
            print(str(re))
            # TODO delete shock node
            raise

        # STEP 6: contruct the output to send back
        returnVal = {'report_name': report_info['name'], 'report_ref': report_info['ref']}

        #END run_filter_contigs_by_length

        # At some point might do deeper type checking...
        if not isinstance(returnVal, dict):
            raise ValueError('Method run_filter_contigs_by_length return value ' +
                             'returnVal is not type dict as required.')
        # return the results
        return [returnVal]

    def run_fractionate_contigs(self, ctx, params):
        """
        :param params: instance of type "Fractionate_Contigs_Params"
           (fractionate_contigs() ** **  Split Assemblies into
           Presence/Absence with respect to other objects) -> structure:
           parameter "workspace_name" of type "workspace_name" (** The
           workspace object refs are of form: ** **    objects =
           ws.get_objects([{'ref':
           params['workspace_id']+'/'+params['obj_name']}]) ** ** "ref" means
           the entire name combining the workspace id and the object name **
           "id" is a numerical identifier of the workspace or object, and
           should just be used for workspace ** "name" is a string identifier
           of a workspace or object.  This is received from Narrative.),
           parameter "input_assembly_ref" of type "data_obj_ref", parameter
           "input_pos_filter_obj_refs" of type "data_obj_name", parameter
           "output_name" of type "data_obj_name", parameter
           "fractionate_mode" of String
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: returnVal
        #BEGIN run_fractionate_contigs
        #END run_fractionate_contigs

        # At some point might do deeper type checking...
        if not isinstance(returnVal, dict):
            raise ValueError('Method run_fractionate_contigs return value ' +
                             'returnVal is not type dict as required.')
        # return the results
        return [returnVal]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
