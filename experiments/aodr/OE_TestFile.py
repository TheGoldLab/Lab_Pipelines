from pyramid import cli

pyramidSearchPath = "/Users/lowell/Documents/GitHub/Lab_Matlab_Utilities/dataSession/test/pyramid/"
convertSpecs = "AODR_test_nwb_experiment.yaml"
event_file = "/Users/lowell/Library/CloudStorage/Box-Box/GoldLab/Data/Physiology/AODR/Recordings/Testing/Anubis_2024-03-29_12-36-19" #"/Users/lowell/Data/Physiology/AODR/Data/Anubis/Raw/Unsorted/OE_Test_Events.csv"
output_fname = "/Users/lowell/Data/Physiology/AODR/Data/Anubis/Converted/Unsorted/Pyramid/OE_Test_Pyramid_Out.hdf5"

cli.main(["convert", 
          "--trial-file", output_fname, 
          "--search-path", pyramidSearchPath, 
          "--experiment", convertSpecs, 
          "--readers", 
          "event_reader.nwb_file="+event_file,
          "gaze_x_reader.nwb_file="+event_file,
          "gaze_y_reader.nwb_file="+event_file])

 