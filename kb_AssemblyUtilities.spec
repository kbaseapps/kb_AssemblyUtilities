/*
A KBase module: kb_AssemblyUtilities
*/

module kb_AssemblyUtilities {
    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;


    /* 
    ** The workspace object refs are of form:
    **
    **    objects = ws.get_objects([{'ref': params['workspace_id']+'/'+params['obj_name']}])
    **
    ** "ref" means the entire name combining the workspace id and the object name
    ** "id" is a numerical identifier of the workspace or object, and should just be used for workspace
    ** "name" is a string identifier of a workspace or object.  This is received from Narrative.
    */
    typedef string workspace_name;
    typedef string sequence;
    typedef string data_obj_name;
    typedef string data_obj_ref;
    typedef int    bool;    


    /* filter_contigs_by_length()
    **
    **  Remove Contigs that are under a minimum threshold
    */
    typedef structure {
        workspace_name workspace_name;
        data_obj_ref   input_assembly_refs;   /* Assemblies or AssemblySets */
        int            min_contig_length;
        data_obj_name  output_name;
    } Filter_Contigs_by_Length_Params;

    funcdef run_filter_contigs_by_length (Filter_Contigs_by_Length_Params params)  returns (ReportResults) authentication required;    


    /* fractionate_contigs()
    **
    **  Split Assemblies into Presence/Absence with respect to other objects
    */
    typedef structure {
        workspace_name workspace_name;
        data_obj_ref   input_assembly_ref;   /* Assembly or AMA */
        data_obj_name  input_pos_filter_obj_refs;
        data_obj_name  output_name;
	string         fractionate_mode;
    } Fractionate_Contigs_Params;

    typedef structure {
        string report_name;
        string report_ref;
	int    source_contigs_count;
	int    positive_contigs_count;
	int    negative_contigs_count;
	int    source_contigs_sum_length;
	int    positive_contigs_sum_length;
	int    negative_contigs_sum_length;
	int    source_contigs_feature_count;
	int    positive_contigs_feature_count;
	int    negative_contigs_feature_count;
    } Fractionate_Contigs_Results;

    funcdef run_fractionate_contigs (Fractionate_Contigs_Params params)  returns (Fractionate_Contigs_Results) authentication required;    


    /* assembly_depth_of_coverage_with_bbmap()
    **
    **  get the per contig and whole assembly average depth of coverage
    */
    typedef structure {
        workspace_name workspace_name;
        list<data_obj_ref> input_assembly_refs;   /* Assembly, AssemblySet, Genome, GenomeSet, or AMA */
        list<data_obj_ref> input_reads_refs;   /* Reads */
    } Assembly_Depth_of_Coverage_with_BBMap_Params;

    typedef structure {
        string report_name;
        string report_ref;
	mapping<string,string> run_metadata;
	list<string> input_reads_names; 
	mapping<string,mapping<string,int>> input_reads_stats;
	mapping<string,mapping<string,int>> contig_stats;
	mapping<string,mapping<string,int>> assembly_stats;
	mapping<string,list<float>> contig_avg_doc;
	mapping<string,list<float>> assembly_avg_doc;
    } Assembly_Depth_of_Coverage_with_BBMap_Results;

    funcdef run_assembly_depth_of_coverage_with_bbmap (Assembly_Depth_of_Coverage_with_BBMap_Params params)  returns (Assembly_Depth_of_Coverage_with_BBMap_Results) authentication required;    

};
