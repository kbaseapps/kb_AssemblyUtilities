# -*- coding: utf-8 -*-
import os
import time
import unittest
import json
import requests
import shutil
from pprint import pprint  # noqa: F401
from configparser import ConfigParser

from kb_AssemblyUtilities.kb_AssemblyUtilitiesImpl import kb_AssemblyUtilities
from kb_AssemblyUtilities.kb_AssemblyUtilitiesServer import MethodContext
from kb_AssemblyUtilities.authclient import KBaseAuth as _KBaseAuth

from installed_clients.WorkspaceClient import Workspace
from installed_clients.AssemblyUtilClient import AssemblyUtil
from installed_clients.GenomeFileUtilClient import GenomeFileUtil
from installed_clients.MetagenomeUtilsClient import MetagenomeUtils
from installed_clients.SetAPIServiceClient import SetAPI

class kb_AssemblyUtilitiesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = os.environ.get('KB_AUTH_TOKEN', None)
        config_file = os.environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('kb_AssemblyUtilities'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'kb_AssemblyUtilities',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = Workspace(cls.wsURL)
        cls.serviceImpl = kb_AssemblyUtilities(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']
        suffix = int(time.time() * 1000)
        cls.wsName = "test_kb_AssemblyUtilities_" + str(suffix)
        ret = cls.wsClient.create_workspace({'workspace': cls.wsName})  # noqa

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    def getWsClient(self):
        return self.__class__.wsClient

    def getWsName(self):
        if hasattr(self.__class__, 'wsName'):
            return self.__class__.wsName
        suffix = int(time.time() * 1000)
        wsName = "test_kb_assembly_compare_" + str(suffix)
        ret = self.getWsClient().create_workspace({'workspace': wsName})  # noqa
        self.__class__.wsName = wsName
        return wsName

    def getImpl(self):
        return self.__class__.serviceImpl
            
    def getContext(self):
        return self.__class__.ctx

            
    ##############
    # UNIT TESTS #
    ##############

    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa

    #### test_filter_contigs_by_length_01()
    ##
    @unittest.skip("skipped test_filter_contigs_by_length_01()")  # uncomment to skip
    def test_filter_contigs_by_length_01 (self):
        method = 'filter_contigs_by_length_01'
        
        print ("\n\nRUNNING: test_filter_contigs_by_length_01()")
        print ("===========================================\n\n")

        # upload test data
        try:
            auClient = AssemblyUtil(self.callback_url, token=self.getContext()['token'])
        except Exception as e:
            raise ValueError('Unable to instantiate auClient with callbackURL: '+ self.callback_url +' ERROR: ' + str(e))
        ass_file_1 = 'assembly_1.fa'
        ass_file_2 = 'assembly_2.fa'
        ass_path_1 = os.path.join(self.scratch, ass_file_1)
        ass_path_2 = os.path.join(self.scratch, ass_file_2)
        shutil.copy(os.path.join("data", ass_file_1), ass_path_1)
        shutil.copy(os.path.join("data", ass_file_2), ass_path_2)
        ass_ref_1 = auClient.save_assembly_from_fasta({
            'file': {'path': ass_path_1},
            'workspace_name': self.getWsName(),
            'assembly_name': 'assembly_1'
        })
        ass_ref_2 = auClient.save_assembly_from_fasta({
            'file': {'path': ass_path_2},
            'workspace_name': self.getWsName(),
            'assembly_name': 'assembly_2'
        })

        # run method
        input_refs = [ ass_ref_1, ass_ref_2 ]
        base_output_name = method+'_output'
        params = {
            'workspace_name': self.getWsName(),
            'input_assembly_refs': input_refs,
            'min_contig_length': 1000,
            'output_name': 'test_filtered'
        }
        result = self.getImpl().run_filter_contigs_by_length(self.getContext(),params)
        print('RESULT:')
        pprint(result)
        pass


    #### test_fractionate_contigs_pos_filter_ASSEMBLY_ASSEMBLY_01()
    ##
    @unittest.skip("skipped test_fractionate_contigs_ASSEMBLY_ASSEMBLY_01()")  # uncomment to skip
    def test_fractiontate_contigs_ASSEMBLY_ASSEMBLY_01 (self):
        method = 'fractionate_contigs_pos_filter_ASSEMBLY_ASSEMBLY_01'
        
        print ("\n\nRUNNING: test_"+method+"()")
        print ("==========================================================\n\n")

        # upload test data
        try:
            auClient = AssemblyUtil(self.callback_url, token=self.getContext()['token'])
        except Exception as e:
            raise ValueError('Unable to instantiate auClient with callbackURL: '+ self.callback_url +' ERROR: ' + str(e))
        base_1 = 'assembly_1plus2'
        base_2 = 'assembly_2'
        type_1 = 'Assembly'
        type_2 = 'Assembly'
        ass_file_1_fa = base_1+'.fa'
        ass_file_2_fa = base_2+'.fa'
        ass_path_1_fa = os.path.join(self.scratch, ass_file_1_fa)
        ass_path_2_fa = os.path.join(self.scratch, ass_file_2_fa)
        shutil.copy(os.path.join("data", ass_file_1_fa), ass_path_1_fa)
        shutil.copy(os.path.join("data", ass_file_2_fa), ass_path_2_fa)
        ass_ref_1 = auClient.save_assembly_from_fasta({
            'file': {'path': ass_path_1_fa},
            'workspace_name': self.getWsName(),
            'assembly_name': base_1+'.'+type_1
        })
        ass_ref_2 = auClient.save_assembly_from_fasta({
            'file': {'path': ass_path_2_fa},
            'workspace_name': self.getWsName(),
            'assembly_name': base_2+'.'+type_2
        })

        # run method
        base_output_name = method+'_output'
        fractionate_mode = 'both'
        params = {
            'workspace_name': self.getWsName(),
            'input_assembly_ref': ass_ref_1,
            'input_pos_filter_obj_refs': [ass_ref_2],
            'fractionate_mode': fractionate_mode,
            'output_name': 'test_fractionated'+'-'+base_1+'.'+type_1+'-'+base_2+'.'+type_2+'-'+fractionate_mode
        }
        result = self.getImpl().run_fractionate_contigs(self.getContext(),params)
        print('RESULT:')
        pprint(result)
        pass


    #### test_fractionate_contigs_pos_filter_AMA_ASSEMBLY_01()
    ##
    # HIDE @unittest.skip("skipped test_fractionate_contigs_AMA_ASSEMBLY_01()")  # uncomment to skip
    def test_fractiontate_contigs_AMA_ASSEMBLY_01 (self):
        method = 'fractionate_contigs_pos_filter_AMA_ASSEMBLY_01'
        
        print ("\n\nRUNNING: test_"+method+"()")
        print ("==========================================================\n\n")

        # upload test data
        try:
            auClient = AssemblyUtil(self.callback_url, token=self.getContext()['token'])
        except Exception as e:
            raise ValueError('Unable to instantiate auClient with callbackURL: '+ self.callback_url +' ERROR: ' + str(e))
        try:
            gfuClient = GenomeFileUtil(self.callback_url, token=self.getContext()['token'])
        except Exception as e:
            raise ValueError('Unable to instantiate gfuClient with callbackURL: '+ self.callback_url +' ERROR: ' + str(e))

        base_1 = 'assembly_1plus2'
        base_2 = 'assembly_2'
        type_1 = 'AMA'
        type_2 = 'Assembly'
        ass_file_1_fa = base_1+'.fa'
        ass_file_1_gff = base_1+'.gff'
        ass_file_2_fa = base_2+'.fa'
        ass_path_1_fa = os.path.join(self.scratch, ass_file_1_fa)
        ass_path_1_gff = os.path.join(self.scratch, ass_file_1_gff)
        ass_path_2_fa = os.path.join(self.scratch, ass_file_2_fa)
        shutil.copy(os.path.join("data", ass_file_1_fa), ass_path_1_fa)
        shutil.copy(os.path.join("data", ass_file_1_gff), ass_path_1_gff)
        shutil.copy(os.path.join("data", ass_file_2_fa), ass_path_2_fa)
        ass_ref_1 = gfuClient.fasta_gff_to_metagenome({
            'fasta_file': {'path': ass_path_1_fa},
            'gff_file': {'path': ass_path_1_gff},
            'generate_missing_genes': 1,
            'source': 'GFF',
            'scientific_name': base_1,
            'workspace_name': self.getWsName(),
            'genome_name': base_1+'.'+type_1
        }).get('metagenome_ref')
        ass_ref_2 = auClient.save_assembly_from_fasta({
            'file': {'path': ass_path_2_fa},
            'workspace_name': self.getWsName(),
            'assembly_name': base_2+'.'+type_2
        })

        # run method
        base_output_name = method+'_output'
        fractionate_mode = 'both'
        params = {
            'workspace_name': self.getWsName(),
            'input_assembly_ref': ass_ref_1,
            'input_pos_filter_obj_refs': [ass_ref_2],
            'fractionate_mode': fractionate_mode,
            'output_name': 'test_fractionated'+'-'+base_1+'.'+type_1+'-'+base_2+'.'+type_2+'-'+fractionate_mode
        }
        result = self.getImpl().run_fractionate_contigs(self.getContext(),params)
        print('RESULT:')
        pprint(result)
        pass
