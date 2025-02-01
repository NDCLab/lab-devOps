function [] = MADE_pipeline(dataset, subjects, session)

%%to Run on FIU HPC%

% start matlabpool with max workers set in the slurm file
N_CPUS = str2double(getenv('SLURM_CPUS_PER_TASK'));

if isnan(N_CPUS) || N_CPUS <= 0
    N_CPUS = max(1, feature('numcores')); % fallback value
    warning('SLURM_CPUS_PER_TASK not set or invalid. Using %d worker(s).', N_CPUS);
end

% create a local cluster object
cluster = parcluster('local');
cluster.NumWorkers = N_CPUS;

if ~isempty(gcp('nocreate'))
    delete(gcp);
end

parpool(cluster, N_CPUS)

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% This script was initially edited by George Buzzell for the NDC Lab EEG
% Training Workshop on 10/21, then modified by George Buzzell and Kianoosh Hosseini to preprocess THRIVE dataset.
%
%
% ************************************************************************
% The Maryland Analysis of Developmental EEG (MADE) Pipeline
% Version 1.0
% Developed at the Child Development Lab, University of Maryland, College Park

% Contributors to MADE pipeline:
% Ranjan Debnath (rdebnath@umd.edu)
% George A. Buzzell (gbuzzell@umd.edu)
% Santiago Morales Pamplona (moraless@umd.edu)
% Stephanie Leach (sleach12@umd.edu)
% Maureen Elizabeth Bowers (mbowers1@umd.edu)
% Nathan A. Fox (fox@umd.edu)

% MADE uses EEGLAB toolbox and some of its plugins. Before running the pipeline, you have to install the following:
% EEGLab:  https://sccn.ucsd.edu/eeglab/downloadtoolbox.php/download.php

% You also need to download the following plugins/extensions from here: https://sccn.ucsd.edu/wiki/EEGLAB_Extensions
% Specifically, download:
% MFFMatlabIO: https://github.com/arnodelorme/mffmatlabio/blob/master/README.txt
% FASTER: https://sourceforge.net/projects/faster/
% ADJUST:  https://www.nitrc.org/projects/adjust/ [Maybe we will replace this with our own GitHub link?]

% After downloading these plugins (as zip files), you need to place it in the eeglab/plugins folder.
% For instance, for FASTER, you uncompress the downloaded extension file (e.g., 'FASTER.zip') and place it in the main EEGLAB "plugins" sub-directory/sub-folder.
% After placing all the required plugins, add the EEGLAB folder to your path by using the following code:

% addpath(genpath(('...')) % Enter the path of the EEGLAB folder in this line
% Please cite the following references for in any manuscripts produced utilizing MADE pipeline:

% EEGLAB: A Delorme & S Makeig (2004) EEGLAB: an open source toolbox for
% analysis of single-trial EEG dynamics. Journal of Neuroscience Methods, 134, 9?21.

% firfilt (filter plugin): developed by Andreas Widmann (https://home.uni-leipzig.de/biocog/content/de/mitarbeiter/widmann/eeglab-plugins/)

% FASTER: Nolan, H., Whelan, R., Reilly, R.B., 2010. FASTER: Fully Automated Statistical
% Thresholding for EEG artifact Rejection. Journal of Neuroscience Methods, 192, 152?162.

% ADJUST: Mognon, A., Jovicich, J., Bruzzone, L., Buiatti, M., 2011. ADJUST: An automatic EEG
% artifact detector based on the joint use of spatial and temporal features. Psychophysiology, 48, 229?240.
% Our group has modified ADJUST plugin to improve selection of ICA components containing artifacts

% This pipeline is released under the GNU General Public License version 3.

% ************************************************************************

%% User input: user provide relevant information to be used for data processing
% Preprocessing of EEG data involves using some common parameters for
% every subject. This part of the script initializes the common parameters.

clc % clear matlab command window

%% MUST EDIT THIS
%running in "EEG_training" folder on your computer
main_dir = strcat("/home/data/NDClab/datasets/", dataset); %directory on the HPC
main_dir = char(main_dir);

%% Setting up other things

%Location of MADE and ADJUSTED-ADJUST scripts
%addpath(genpath([main_dir filesep 'code' filesep 'eeg_preprocessing']));% enter the path of the folder in this line
addpath(genpath('/home/data/NDClab/tools/lab-devOps/scripts/MADE_pipeline_standard/eeg_preprocessing'));% enter the path of the folder in this line

%Location of EEGlab
%addpath(genpath([main_dir filesep 'code' filesep 'eeglab13_4_4b']));% enter the path of the EEGLAB folder in this line
addpath(genpath('/home/data/NDClab/tools/lab-devOps/scripts/MADE_pipeline_standard/eeglab13_4_4b'));% enter the path of the EEGLAB folder in this line

%remove path to octave functions inside matlab to prevent errors when
%rmpath([main_dir filesep 'code' filesep 'eeglab13_4_4b' filesep 'functions' filesep 'octavefunc' filesep 'signal'])
rmpath(['/home/data/NDClab/tools/lab-devOps/scripts/MADE_pipeline_standard/eeglab13_4_4b' filesep 'functions' filesep 'octavefunc' filesep 'signal'])

% 1. Enter the path of the folder that has the raw data to be analyzed
rawdata_location_parent = strcat(main_dir, '/sourcedata/raw/', session, '/eeg');
rawdata_location_parent = char(rawdata_location_parent);

% 2. Enter the path of the channel location file
%channel_locations = loadbvef('/home/data/NDClab/datasets/thrive-dataset/code/thrive_eeg/chan_locs_files/electrode_locs_files/CACS-128-X7-FIXED-64only.bvef');
%channel_locations = loadbvef(strcat(main_dir, '/code/eeg_preprocessing/chan_locs_files/electrode_locs_files/CACS-128-X7-FIXED-64only.bvef'));
channel_locations = loadbvef('/home/data/NDClab/tools/lab-devOps/scripts/MADE_pipeline_standard/eeg_preprocessing/chan_locs_files/electrode_locs_files/CACS-128-X7-FIXED-64only.bvef');

%need to modify for social vs nonsocial

% STIMULUS TRIGGERS
% passage text appears on-screen: 11
% passage text disappears (participant proceeded to the next screen): 10
% challenge text appears on-screen: 21
%
% RESPONSE TRIGGERS
% error response to challenge question: 30
% correct response to challenge question: 31

stimulus_markers = {'S  1', 'S  2', 'S  3', 'S  4', 'S 41', 'S 42', 'S 43', ...
    'S 44', 'S 51', 'S 52', 'S 53', 'S 54'};      % enter the stimulus markers that need to be adjusted for time offset
response_markers = {};       % enter the response makers that need to be adjusted for time offset

% 5. Do you want to down sample the data?
down_sample = 1; % 0 = NO (no down sampling), 1 = YES (down sampling)
sampling_rate = 1000; % set sampling rate (in Hz), if you want to down sample

% 6. Do you want to delete the outer layer of the channels? (Rationale has been described in MADE manuscript)
%    This fnction can also be used to down sample electrodes. For example, if EEG was recorded with 128 channels but you would
%    like to analyse only 64 channels, you can assign the list of channnels to be excluded in the 'outerlayer_channel' variable.
%    Can also use this to remove ocular channels if they are in non-standard
%    locations
delete_outerlayer = 0; % 0 = NO (do not delete outer layer), 1 = YES (delete outerlayer);
% If you want to delete outer layer, make a list of channels to be deleted
outerlayer_channel = {'16','15','12','13','8','31','26','25','30','32','60','64','61','62','56','57','63','41','46','45','48'}; % list of channels

% 7. Initialize the filters
highpass = .1; % High-pass frequency
lowpass  = 49; % Low-pass frequency. We recommend low-pass filter at/below line noise frequency (see manuscript for detail)

% 8. Are you processing task-related or resting-state EEG data?
task_eeg = 1; % 0 = resting, 1 = task
task_event_markers = {'S  1', 'S  2', 'S  3', 'S  4', 'S 41', 'S 42', 'S 43', ...
    'S 44', 'S 51', 'S 52', 'S 53', 'S 54', 'S 11', 'S 12', 'S 21', 'S 22'}; % enter all the event/condition markers (i.e., stim + resp markers)

% 9. Do you want to epoch/segment your data?
epoch_data = 1; % 0 = NO (do not epoch), 1 = YES (epoch data)
task_epoch_length = [-1 2]; % epoch length in second
dummy_events ={'999'}; % enter dummy events name

% 10. Do you want to remove/correct baseline?
remove_baseline = 1; % 0 = NO (no baseline correction), 1 = YES (baseline correction)
baseline_window = []; % baseline period in milliseconds (MS) [] = entire epoch

% 11. Do you want to remove artifact laden epoch based on voltage threshold?
voltthres_rejection = 1; % 0 = NO, 1 = YES
volt_threshold = [-125 125]; % lower and upper threshold (in ?V)

% 12. Do you want to perform epoch level channel interpolation for artifact laden epoch? (see manuscript for detail)
interp_epoch = 1; % 0 = NO, 1 = YES.
frontal_channels = {'14','11','10','43','44','47'}; % If you set interp_epoch = 1, enter the list of frontal channels to check (see manuscript for detail)

%13. Do you want to interpolate the bad channels that were removed from data?
interp_channels = 1; % 0 = NO (Do not interpolate), 1 = YES (interpolate missing channels)

% 14. Do you want to rereference your data?
rerefer_data = 1; % 0 = NO, 1 = YES
reref=[]; % Enter electrode name/s or number/s to be used for rereferencing
% For channel name/s enter, reref = {'channel_name', 'channel_name'};
% For channel number/s enter, reref = [channel_number, channel_number];
% For average rereference enter, reref = []; default is average rereference

% 15. Do you want to save interim results?
save_interim_result = 1; % 0 = NO (Do not save) 1 = YES (save interim results)

% 16. How do you want to save your data? .set or .mat
output_format = 1; % 1 = .set (EEGLAB data structure), 2 = .mat (Matlab data structure)

% ********* no need to edit beyond this point for EGI .mff data **********
% ********* for non-.mff data format edit data import function ***********
% ********* below using relevant data import plugin from EEGLAB **********


% List subject folders under EEG folder
cd (rawdata_location_parent)
subjects_to_process = string(split(subjects, "/"));
subjects_to_process = subjects_to_process(subjects_to_process~=""); %nvm not necessary
subjects_to_process = strcat("sub-", subjects_to_process);

% if job was run as a task array, divide up subjects; otherwise, process everyone

subjects_to_process = all_subjects;
n_tasks = str2double(getenv('SLURM_ARRAY_TASK_COUNT'));
task_idx = str2double(getenv('SLURM_ARRAY_TASK_ID')); % index must start at 1

if ~isnan(n_tasks) && ~isnan(task_idx) && n_tasks >= 1 && task_idx >= 1
    % Ensure valid task index
    if task_idx > n_tasks
        error('Task index %d exceeds array task count %d', task_idx, n_tasks);
    end
    
    subject_count = length(all_subjects);
    subject_indices = 1:subject_count;
    
    % take all subjects where subIndex = taskCount mod taskIndex
    % (remember to adjust for MATLAB's 1-based indexing)
    process_subject = (mod(subject_indices - 1, n_tasks) == (task_idx - 1));
    subjects_to_process = all_subjects(process_subject);
    
    fprintf('Task %d/%d processing %d subjects\n', ...
        task_idx, n_tasks, length(subjects_to_process));
else
    % Default case: process all subjects if not in a task array
    fprintf('Processing all %d subjects\n', length(subjects_to_process));
end


%for file_locater_counter = 1:length(subjects_to_process) % This for loop lists the folders containing the main data files
for file_locater_counter = 1:length(subjects_to_process)
    try
        subjStart = tic;
        rawdata_location = fullfile(rawdata_location_parent, subjects_to_process(file_locater_counter));
        rawdata_location = char(rawdata_location);
        if ~isfolder(rawdata_location)
            warning(['Cannot find ' char(subjects_to_process(file_locater_counter)) ' folder in ' rawdata_location_parent ', skipping.']);
            continue
        end
        
        % Read files to analyses
        datafile_names=dir([rawdata_location filesep '*.vhdr']);
        datafile_names=datafile_names(~ismember({datafile_names.name},{'.', '..', '.DS_Store'}));
        datafile_names={datafile_names.name};
        %[filepath,name,ext] = fileparts(char(datafile_names{1}));
        if isempty(datafile_names)
            %warning(['Cannot find vhdr file / files in ' rawdata_location ', skipping.']);
            %continue
            error(['Cannot find vhdr file / files in ' rawdata_location ', skipping.']);
        end
        
        % Enter the path of the folder where you want to save the processed data
        output_location = fullfile(main_dir, "derivatives", "preprocessed", subjects_to_process(file_locater_counter), session, "eeg" );
        % update the output_location
        output_location = char(output_location);
        
        % write each sub to different logfile in output dir
        [~, vhdr_file, ~] = fileparts(subjects_to_process(file_locater_counter));
        if exist([output_location filesep 'MADE_logfiles'], 'dir') == 0
            mkdir([output_location filesep 'MADE_logfiles'])
        end
        dfile=fullfile(output_location, 'MADE_logfiles', [char(vhdr_file) '_' datestr(now,'mm-dd-yyyy_HH:MM:SS') '.log']);
        diary(dfile)
        
        corrected=dir([rawdata_location filesep 'deviation.txt']);
        if ~isempty({corrected.name})
            corrected=1
            devFile = readlines([rawdata_location filesep 'deviation.txt']);
            vhdrFound = 0;
            for i = 1:length(devFile)
                if startsWith(lower(devFile(i)), "files to process:")
                    line = devFile(i).split(':');
                    filesToProcess = strip(line(2).split(','));
                    filesToProcess = filesToProcess(endsWith(filesToProcess(:), "vhdr")); %only need vhdrs
                    vhdrFound = 1;
                end
            end
            if vhdrFound
                datafile_names = cellstr(filesToProcess');
            else
                datafile_names = {};
            end
        else
            corrected=0
        end
        
        
        
        %% Check whether EEGLAB and all necessary plugins are in Matlab path.
        if exist('eeglab','file')==0
            error(['Please make sure EEGLAB is on your Matlab path. Please see EEGLAB' ...
                'wiki page for download and instalation instructions']);
        end
        
        if exist('pop_firws', 'file')==0
            error(['Please make sure  "firfilt" plugin is in EEGLAB plugin folder and on Matlab path.' ...
                ' Please see EEGLAB wiki page for download and instalation instructions of plugins.']);
        end
        
        if exist('channel_properties', 'file')==0
            error(['Please make sure "FASTER" plugin is in EEGLAB plugin folder and on Matlab path.' ...
                ' Please see EEGLAB wiki page for download and instalation instructions of plugins.']);
        end
        
        if exist('ADJUST', 'file')==0
            error(['Please make sure you download modified "ADJUST" plugin from GitHub (link is in MADE manuscript)' ...
                ' and ADJUST is in EEGLAB plugin folder and on Matlab path.']);
        end
        
        %% Create output folders to save data
        if exist(output_location, 'dir') == 0
            mkdir(output_location)
        end
        
        %% Initialize output variables
        reference_used_for_faster=[]; % reference channel used for running faster to identify bad channel/s
        faster_bad_channels=[]; % number of bad channel/s identified by faster
        ica_preparation_bad_channels=[]; % number of bad channel/s due to channel/s exceeding xx% of artifacted epochs
        length_ica_data=[]; % length of data (in second) fed into ICA decomposition
        total_ICs=[]; % total independent components (ICs)
        ICs_removed=[]; % number of artifacted ICs
        total_epochs_before_artifact_rejection=[];
        total_epochs_after_artifact_rejection=[];
        total_channels_interpolated=[]; % total_channels_interpolated=faster_bad_channels+ica_preparation_bad_channels
        
        
        %% Loop over all data files
        
        % switch to output directory
        cd(output_location);
        
        for subject=1:length(datafile_names)
            % "subject" is actually task, subjects_to_process are subjects
            %[filepath,name,ext] = fileparts(char(datafile_names{subject}));
            vhdr_filename = datafile_names{subject};
            filename_re = regexp(datafile_names{subject}, '^(sub-[0-9]+)_([a-zA-Z0-9_-]+)_(s[0-9]+_r[0-9]+_e[0-9]+)(\.[a-z0-9]+)$', 'tokens');
            if isempty(filename_re) && corrected == 0
                warning(['File name ' datafile_names{subject} ' in ' rawdata_location ' does not match conventions, skipping.']);
                continue
                % EEG files with a deviation.txt in the folder may have an additional description before ".vhdr" and after "s1_r1_e1"
            elseif isempty(filename_re) && corrected == 1
                filename_re = regexp(datafile_names{subject}, '^(sub-[0-9]+)_([a-zA-Z0-9_-]+)_(s[0-9]+_r[0-9]+_e[0-9]+)_?([a-zA-Z0-9_-]*)(\.[a-z0-9]+)$', 'tokens');
                if isempty(filename_re)
                    warning(['File name ' datafile_names{subject} ' in ' rawdata_location ' does not match conventions, skipping.']);
                    continue
                else
                    [subj, task, sess, desc, ext] = filename_re{1}{:};
                    if isempty(desc)
                        output_report_path = [output_location filesep 'MADE_preprocessing_report_' task '_' sess];
                    else
                        output_report_path = [output_location filesep 'MADE_preprocessing_report_' task '_' sess '_' desc];
                        desc = ['_' desc];
                    end
                end
            else
                [subj, task, sess, ext] = filename_re{1}{:};
                desc = '';
            end
            
            %% Initialize EEG structurem, output variables, and report table
            EEG=[]; %initialize eeg structure
            report_table = []; %report table that will be created and writen to disk (appended) after processing completes for this participant
            reference_used_for_faster=[]; % reference channel used for running faster to identify bad channel/s
            faster_bad_channels=[]; % number of bad channel/s identified by faster
            ica_preparation_bad_channels=[]; % number of bad channel/s due to channel/s exceeding xx% of artifacted epochs
            length_ica_data=[]; % length of data (in second) fed into ICA decomposition
            total_ICs=[]; % total independent components (ICs)
            ICs_removed=[]; % number of artifacted ICs
            total_epochs_before_artifact_rejection=[];
            total_epochs_after_artifact_rejection=[];
            total_channels_interpolated=[]; % total_channels_interpolated=faster_bad_channels+ica_preparation_bad_channels
            
            
            fprintf('\n\n\n*** Processing subject %d (%s) ***\n\n\n', subject, datafile_names{subject});
            
            %% STEP 1: Import EEG data file and relevant information
            
            %load in raw data
            EEG = pop_loadbv(rawdata_location, datafile_names{subject});
            EEG = eeg_checkset(EEG);
            
            %% STEP 4: Change sampling rate
            if down_sample==1
                if floor(sampling_rate) > EEG.srate
                    error ('Sampling rate cannot be higher than recorded sampling rate');
                elseif floor(sampling_rate) ~= EEG.srate
                    EEG = pop_resample( EEG, sampling_rate);
                    EEG = eeg_checkset( EEG );
                end
            end
            
            %make a copy of GSR and sync channels, then delete from eeg structure
            
            gsrChan = EEG.data(64, :);
            EEG = pop_select( EEG,'nochannel', 64);
            EEG = eeg_checkset( EEG );
            
            syncChan = EEG.data(64, :);
            EEG = pop_select( EEG,'nochannel', 64);
            EEG = eeg_checkset( EEG );
            %[ALLEEG EEG CURRENTSET] = eeg_store(ALLEEG, EEG, CURRENTSET);
            
            
            
            %add in ref channels
            origData = EEG.data;
            [origData_NumRows, origData_NumCols] = size(origData);
            EEG.data = NaN(origData_NumRows+1, origData_NumCols);
            EEG.data(1,:) = 0; %add ref as zeros
            EEG.data(2:end,:) = origData; %copy over orig EEG data
            %%%
            %delete ground from newChanLocs
            modNewChanlocs = channel_locations(2:end);
            
            %replace chanlocs with
            EEG.chanlocs = modNewChanlocs;
            EEG.nbchan = EEG.nbchan+1;
            %%%%
            EEG = eeg_checkset( EEG );
            %[ALLEEG EEG CURRENTSET] = eeg_store(ALLEEG, EEG, CURRENTSET);
            
            
            
            EEG = eeg_checkset( EEG );
            %[ALLEEG EEG CURRENTSET] = eeg_store(ALLEEG, EEG, CURRENTSET);
            
            %update/refresh eeglab and plot
            %eeglab redraw
            
            % Check whether the channel locations were properly imported. The EEG signals and channel numbers should be same.
            if size(EEG.data, 1) ~= length(EEG.chanlocs)
                error('The size of the data does not match with channel numbers.');
            end
            
            %% STEP 1b: convert all type field markers to string (if not already)
            
            %loop through all the type markes, if numeric, convert to string
            % (Given that this script assumes that "type" field markers are strings, we need to
            % convert all type field markers to string, in case they are not
            % already)
            for atm=1:length({EEG.event.type})
                if isnumeric(EEG.event(atm).type)
                    EEG.event(atm).type = num2str(EEG.event(atm).type);
                end
            end
            
            
            %% STEP 5: Delete outer layer of channels
            chans_labels=cell(1,EEG.nbchan);
            for i=1:EEG.nbchan
                chans_labels{i}= EEG.chanlocs(i).labels;
            end
            
            if delete_outerlayer==1
                [chans,chansidx] = ismember(outerlayer_channel, chans_labels);
                outerlayer_channel_idx = chansidx(chansidx ~= 0);
                if isempty(outerlayer_channel_idx)==1
                    error(['None of the outer layer channels present in channel locations of data.'...
                        ' Make sure outer layer channels are present in channel labels of data (EEG.chanlocs.labels).']);
                else
                    EEG = pop_select( EEG,'nochannel', outerlayer_channel_idx);
                    EEG = eeg_checkset( EEG );
                end
            end
            
            %% STEP 6: Filter data
            % Calculate filter order using the formula: m = dF / (df / fs), where m = filter order,
            % df = transition band width, dF = normalized transition width, fs = sampling rate
            % dF is specific for the window type. Hamming window dF = 3.3
            
            high_transband = highpass; % high pass transition band
            low_transband = 10; % low pass transition band
            
            hp_fl_order = 3.3 / (high_transband / EEG.srate);
            lp_fl_order = 3.3 / (low_transband / EEG.srate);
            
            % Round filter order to next higher even integer. Filter order is always even integer.
            if mod(floor(hp_fl_order),2) == 0
                hp_fl_order=floor(hp_fl_order);
            elseif mod(floor(hp_fl_order),2) == 1
                hp_fl_order=floor(hp_fl_order)+1;
            end
            
            if mod(floor(lp_fl_order),2) == 0
                lp_fl_order=floor(lp_fl_order)+2;
            elseif mod(floor(lp_fl_order),2) == 1
                lp_fl_order=floor(lp_fl_order)+1;
            end
            
            % Calculate cutoff frequency
            high_cutoff = highpass/2;
            low_cutoff = lowpass + (low_transband/2);
            
            % Performing high pass filtering
            EEG = eeg_checkset( EEG );
            
            raw_data = EEG.data;  % Extract data once
            filteredData = zeros(size(raw_data));
            
            % design filter
            [hiPassFilterCoeffs, delay] = firws(hp_fl_order, high_cutoff/(EEG.srate/2), 'high', 'hamming');
            
            % Process each channel as a separate task
            parfor chanIdx = 1:EEG.nbchan
                filteredData(chanIdx, :) = filtfilt(hiPassFilterCoeffs, 1, double(raw_data(chanIdx, :)));
            end
            
            % Compensate for filter delay
            filteredData = filteredData(:, 1:end-delay);
            
            EEG.data = filteredData;
            
            % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % %
            
            % pop_firws() - filter window type hamming ('wtype', 'hamming')
            % pop_firws() - applying zero-phase (non-causal) filter ('minphase', 0)
            
            % Performing low pass filtering
            EEG = eeg_checkset( EEG );
            
            [loPassFilterCoeffs, delay] = firws(lp_fl_order, low_cutoff/(EEG.srate/2), 'low', 'hamming');
            
            raw_data = EEG.data;  % Extract data once
            filteredData = zeros(size(raw_data));
            
            % Process each channel as a separate task
            parfor chanIdx = 1:EEG.nbchan
                filteredData(chanIdx, :) = filtfilt(loPassFilterCoeffs, 1, double(raw_data(chanIdx, :)));
            end
            
            % Compensate for filter delay
            filteredData = filteredData(:, 1:end-delay);
            
            EEG.data = filteredData;
            EEG = eeg_checkset( EEG );
            
            % pop_firws() - transition band width: 10 Hz
            % pop_firws() - filter window type hamming ('wtype', 'hamming')
            % pop_firws() - applying zero-phase (non-causal) filter ('minphase', 0)
            
            %% STEP 7: Run faster to find bad channels
            % First check whether reference channel (i.e. zeroed channels) is present in data
            % reference channel is needed to run faster
            FASTbadChans=[];
            all_chan_bad_FAST=0;
            
            % Extract essential data outside of parfor
            raw_data = EEG.data;
            raw_data = EEG.data;
            srate = EEG.srate;
            chanlocs = EEG.chanlocs;
            numChannels = EEG.nbchan;
            
            ref_chan=find(all(raw_data == 0, 2));
            if numel(ref_chan)>1
                error(['There are more than 1 zeroed channel (i.e. zero value throughout recording) in data.'...
                    ' Only reference channel should be zeroed channel. Delete the zeroed channel/s which is not reference channel.']);
            end
            
            % Preallocate properties array
            list_properties = zeros(numChannels, ?) % TODO Fix this
            
            % Create data package for parallel workers
            dataPackage = struct('data', raw_data, 'srate', srate, 'chanlocs', chanlocs);
            
            
            if ~isempty(ref_chan)
                parfor chanIdx = 1:numChannels
                    try
                        list_properties(chanIdx, :) = channel_properties(dataPackage, chanIdx, ref_chan);
                    catch ME
                        fprintf('Error processing channel %d: %s\n', chanIdx, ME.message);
                        list_properties(chanIdx,:) = NaN;  % Mark failed channels
                    end
                end
                % list_properties = vertcat(list_properties{:});
                % FASTbadIdx=min_z(list_properties);
                % FASTbadChans=find(FASTbadIdx==1);
                % FASTbadChans=FASTbadChans(FASTbadChans~=ref_chan);
                % reference_used_for_faster={EEG.chanlocs(ref_chan).labels};
                % % EEG = pop_select( EEG,'nochannel', ref_chan); % a bug [kia
                % % removed it as George said]
                % EEG = eeg_checkset(EEG);
                % channels_analysed=EEG.chanlocs; % keep full channel locations to use later for interpolation of bad channels
            else
                warning('Reference channel is not present in data. channel 1 will be used as reference channel.');
                
                ref_chan=find(strcmp({EEG.chanlocs.labels}, '1')); % find Cz channel index
                
                parfor chanIdx = 1:numChannels
                    try
                        % Use channel 1 as pseudo-reference
                        list_properties(chanIdx,:) = channel_properties_optimized(...
                            struct('data', temp_data, 'srate', srate, 'chanlocs', chanlocs),...
                            chanIdx, 1);
                    catch ME
                        fprintf('Error channel %d: %s\n', chanIdx, ME.message);
                        list_properties(chanIdx,:) = NaN;
                    end
                end
                
                % EEG_copy=EEG; % make a copy of the dataset
                % EEG_copy = pop_reref( EEG_copy, ref_chan,'keepref','on'); % rerefer to Cz in copied dataset
                % EEG_copy = eeg_checkset(EEG_copy);
                % list_properties = channel_properties(EEG_copy, 1:EEG_copy.nbchan, ref_chan); % run faster on copied dataset
                % FASTbadIdx=min_z(list_properties);
                % FASTbadChans=find(FASTbadIdx==1);
                % channels_analysed=EEG.chanlocs;
                % reference_used_for_faster={EEG.chanlocs(ref_chan).labels};
            end

            % Find bad channels
            validProps = ~any(isnan(list_properties), 2);
            FASTbadIdx = min_z(list_properties(validProps,:));
            FASTbadChans = find(FASTbadChans == 1);
            
            % If FASTER identifies all channels as bad channels, save the dataset
            % at this stage and ignore the remaining of the preprocessing.
            if numel(FASTbadChans)==EEG.nbchan || numel(FASTbadChans)+1==EEG.nbchan
                all_chan_bad_FAST=1;
                warning(['No usable data for datafile', datafile_names{subject}]);
                if output_format==1
                    EEG = eeg_checkset(EEG);
                    %EEG = pop_editset(EEG, 'setname',  strrep(datafile_names{subject}, ext, '_no_usable_data_all_bad_channels'));
                    %EEG = pop_saveset(EEG, 'filename', strrep(datafile_names{subject}, ext, '_no_usable_data_all_bad_channels.set'),'filepath', [output_location filesep 'processed_data' filesep ]); % save .set format
                    EEG = pop_editset(EEG, 'setname', strcat(subj,'_',task,'_no_usable_data_all_bad_epochs_',sess,desc));
                    EEG = pop_saveset(EEG, 'filename', strcat(subj,'_',task,'_no_usable_data_all_bad_epochs_',sess,desc,'.set'),'filepath', [output_location filesep ]); % save .set format
                elseif output_format==2
                    %save([[output_location filesep 'processed_data' filesep ] strrep(datafile_names{subject}, ext, '_no_usable_data_all_bad_channels.mat')], 'EEG'); % save .mat format
                    parsave([[output_location filesep ] strcat(subj,'_',task,'_no_usable_data_all_bad_epochs_',sess,desc,'.mat')], EEG); % save .mat format
                end
            else
                % Reject channels that are bad as identified by Faster
                EEG = pop_select( EEG,'nochannel', FASTbadChans);
                EEG = eeg_checkset(EEG);
                if isscalar(ref_chan)
                    ref_chan=find(any(EEG.data, 2)==0);
                    EEG = pop_select( EEG,'nochannel', ref_chan); % remove reference channel
                end
            end
            
            if numel(FASTbadChans)==0
                faster_bad_channels='0';
            else
                faster_bad_channels=num2str(FASTbadChans');
            end
            
            if all_chan_bad_FAST==1
                faster_bad_channels='0';
                ica_preparation_bad_channels='0';
                length_ica_data=0;
                total_ICs=0;
                ICs_removed='0';
                total_epochs_before_artifact_rejection=0;
                total_epochs_after_artifact_rejection=0;
                total_channels_interpolated=0;
                any_usable_data = 0;
                report_table=table({datafile_names{subject}}, {datetime('now')}, {reference_used_for_faster}, {faster_bad_channels}, {ica_preparation_bad_channels}, {length_ica_data}, ...
                    {total_ICs}, {ICs_removed}, {total_epochs_before_artifact_rejection}, {total_epochs_after_artifact_rejection}, {total_channels_interpolated}, {any_usable_data});
                report_table.Properties.VariableNames={'datafile_names', 'date_processed', 'reference_used_for_faster', 'faster_bad_channels', ...
                    'ica_preparation_bad_channels', 'length_ica_data', 'total_ICs', 'ICs_removed', 'total_epochs_before_artifact_rejection', ...
                    'total_epochs_after_artifact_rejection', 'total_channels_interpolated', 'any_usable_data'};
                writetable(report_table, [output_report_path '.csv'], "WriteMode", "append");
                continue % ignore rest of the processing and go to next subject
            end
            
            %% Save data after running filter and FASTER function, if saving interim results was preferred
            if save_interim_result ==1
                if output_format==1
                    EEG = eeg_checkset( EEG );
                    EEG = pop_editset(EEG, 'setname', strcat(subj,'_',task,'_filtered_data_',sess,desc));
                    EEG = pop_saveset( EEG,'filename',strcat(subj,'_',task,'_filtered_data_',sess,desc,'.set'),'filepath', [output_location filesep]); % save .set format
                elseif output_format==2
                    parsave([[output_location filesep ] strcat(subj,'_',task,'_filtered_data_',sess,desc,'.mat')], EEG); % save .mat format
                end
            end
            
            %% STEP 8: Prepare data for ICA
            EEG_copy = EEG;
            EEG_copy = eeg_checkset(EEG_copy);
            
            % Perform 1Hz high pass filter on copied dataset
            transband = 1;
            fl_cutoff = transband/2;
            fl_order = 3.3 / (transband / EEG.srate);
            fl_order = floor(fl_order) + mod(floor(fl_order)+1, 2); % Ensure even order
            
            [hiPassFilterCoeffs, ~] = firws(fl_order, fl_cutoff/(EEG.srate/2), 'high', 'hamming');
            
            % Apply parallel filtering
            EEG_copy.data = parallel_filter_channels(EEG_copy.data, EEG_copy.srate, hiPassFilterCoeffs);
            EEG_copy = eeg_checkset(EEG_copy);
            
            % Create epochs for resting EEG
            if task_eeg == 0
                EEG_copy.data = parallel_create_epochs(EEG_copy.data, EEG_copy.srate, 1);
                EEG_copy.pnts = size(EEG_copy.data,2);
                EEG_copy.trials = size(EEG_copy.data,3);
                EEG_copy = eeg_checkset(EEG_copy);
            end
            
            %% STEP 14: Artifact rejection
            if voltthres_rejection==1 && interp_epoch==1
                [badChans, EEG.data] = parallel_artifact_detection(EEG, volt_threshold);
            end
            
            %% STEP 15: Channel interpolation
            if interp_channels==1
                EEG.data = parallel_channel_interpolation(EEG, channels_analysed, N_CPUS);
                EEG = eeg_checkset(EEG);
            end
            
            % Find the artifacted epochs across all channels and reject them before doing ICA.
            EEG_copy = pop_eegthresh(EEG_copy,1, 1:EEG_copy.nbchan, vol_thrs(1), vol_thrs(2), EEG_copy.xmin, EEG_copy.xmax,0,0);
            EEG_copy = eeg_checkset(EEG_copy);
            
            % 1         : data type (1: electrode, 0: component)
            % 0         : display with previously marked rejections? (0: no, 1: yes)
            % 0         : reject marked trials? (0: no (but store the  marks), 1:yes)
            
            % Find artifaceted epochs by using power threshold in 20-40Hz frequency band.
            % This method mainly rejects muscle movement (EMG) artifacts.
            EEG_copy = pop_rejspec(EEG_copy, 1,'elecrange', 1:EEG_copy.nbchan, 'method', 'fft', 'threshold', emg_thrs ,'freqlimits', emg_freqs_limit, 'eegplotplotallrej', 0, 'eegplotreject', 0);
            
            % method                : method to compute spectrum (fft)
            % threshold             : [lower upper] threshold limit(s) in dB.
            % freqlimits            : [lower upper] frequency limit(s) in Hz.
            % eegplotplotallrej     : 0 = Do not superpose rejection marks on previous marks stored in the dataset.
            % eegplotreject         : 0 = Do not reject marked trials (but store the  marks).
            
            % Find the number of artifacted epochs and reject them
            EEG_copy = eeg_checkset(EEG_copy);
            EEG_copy = eeg_rejsuperpose(EEG_copy, 1, 1, 1, 1, 1, 1, 1, 1);
            reject_artifacted_epochs=EEG_copy.reject.rejglobal;
            EEG_copy = pop_rejepoch(EEG_copy, reject_artifacted_epochs, 0);
            
            %% STEP 9: Run ICA with parallel processing
            if ~all_bad_channels
                length_ica_data = EEG_copy.trials;
                EEG_copy = eeg_checkset(EEG_copy);
                EEG_copy = parallel_runica(EEG_copy, N_CPUS);
            end
            
            %% Artifact rejection with parallel processing
            if ~all_bad_epochs
                [EEG_copy, rejected_epochs] = parallel_reject_artifacts(EEG_copy, ...
                    vol_thrs, emg_thrs, emg_freqs_limit);
                total_epochs_after_artifact_rejection = EEG_copy.trials;
            end
            
            % Find the ICA weights that would be transferred to the original dataset
            ICA_WINV=EEG_copy.icawinv;
            ICA_SPHERE=EEG_copy.icasphere;
            ICA_WEIGHTS=EEG_copy.icaweights;
            ICA_CHANSIND=EEG_copy.icachansind;
            
            % If channels were removed from copied dataset during preparation of ica, then remove
            % those channels from original dataset as well before transferring ica weights.
            EEG = eeg_checkset(EEG);
            EEG = pop_select(EEG,'nochannel', ica_prep_badChans);
            
            % Transfer the ICA weights of the copied dataset to the original dataset
            EEG.icawinv=ICA_WINV;
            EEG.icasphere=ICA_SPHERE;
            EEG.icaweights=ICA_WEIGHTS;
            EEG.icachansind=ICA_CHANSIND;
            EEG = eeg_checkset(EEG);
            
            %% STEP 10: Run adjust to find artifacted ICA components
            badICs=[]; EEG_copy =[];
            EEG_copy = EEG;
            EEG_copy = eeg_regepochs(EEG_copy,'recurrence', 1, 'limits',[0 1], 'rmbase', NaN, 'eventtype', '999'); % insert temporary marker 1 second apart and create epochs
            EEG_copy = eeg_checkset(EEG_copy);
            
            % if save_interim_result==1
            %     badICs = adjusted_ADJUST(EEG_copy, [[output_location filesep] strrep(datafile_names{subject}, ext, '_adjust_report')]);
            % else
            %     badICs = adjusted_ADJUST(EEG_copy, [[output_location filesep] strrep(datafile_names{subject}, ext, '_adjust_report')]);
            % end
            badICs = adjusted_ADJUST(EEG_copy, [[output_location filesep] strrep(datafile_names{subject}, ext, '_adjust_report')]);
            close all;
            
            % Mark the bad ICs found by ADJUST
            for ic=1:length(badICs)
                EEG.reject.gcompreject(1, badICs(ic))=1;
                EEG = eeg_checkset(EEG);
            end
            total_ICs=size(EEG.icasphere, 1);
            if numel(badICs)==0
                ICs_removed='0';
            else
                ICs_removed=num2str(double(badICs));
            end
            
            %% Save dataset after ICA, if saving interim results was preferred
            if save_interim_result==1
                if output_format==1
                    EEG = eeg_checkset(EEG);
                    EEG = pop_editset(EEG, 'setname',  strcat(subj,'_',task,'_ica_data_',sess,desc));
                    EEG = pop_saveset(EEG, 'filename', strcat(subj,'_',task,'_ica_data_',sess,desc,'.set'),'filepath', [output_location filesep ]); % save .set format
                elseif output_format==2
                    parsave([[output_location filesep ] strcat(subj,'_',task,'_ica_data_',sess,desc,'.mat')], EEG); % save .mat format
                end
            end
            
            %Ran up to here....
            
            %no manual review/selection of ica artifact performed...
            
            
            
            %% STEP 11: Remove artifacted ICA components from data
            all_bad_ICs=0;
            ICs2remove=find(EEG.reject.gcompreject); % find ICs to remove
            
            % If all ICs and bad, save data at this stage and ignore rest of the preprocessing for this subject.
            if numel(ICs2remove)==total_ICs
                all_bad_ICs=1;
                warning(['No usable data for datafile', datafile_names{subject}]);
                if output_format==1
                    EEG = eeg_checkset(EEG);
                    EEG = pop_editset(EEG, 'setname',  strcat(subj,'_',task,'_no_usable_data_all_bad_ICs_',sess,desc));
                    EEG = pop_saveset(EEG, 'filename', strcat(subj,'_',task,'_no_usable_data_all_bad_ICs_',sess,desc,'.set'),'filepath', [output_location filesep ]); % save .set format
                elseif output_format==2
                    parsave([[output_location filesep ] strcat(subj,'_',task,'_no_usable_data_all_bad_ICs_',sess,desc,'.mat')], EEG); % save .mat format
                end
            else
                EEG = eeg_checkset( EEG );
                EEG = pop_subcomp( EEG, ICs2remove, 0); % remove ICs from dataset
            end
            
            if all_bad_ICs==1
                total_epochs_before_artifact_rejection=0;
                total_epochs_after_artifact_rejection=0;
                total_channels_interpolated=0;
                any_usable_data = 0;
                report_table=table({datafile_names{subject}}, {datetime('now')}, {reference_used_for_faster}, {faster_bad_channels}, {ica_preparation_bad_channels}, {length_ica_data}, ...
                    {total_ICs}, {ICs_removed}, {total_epochs_before_artifact_rejection}, {total_epochs_after_artifact_rejection}, {total_channels_interpolated}, {any_usable_data});
                report_table.Properties.VariableNames={'datafile_names', 'date_processed', 'reference_used_for_faster', 'faster_bad_channels', ...
                    'ica_preparation_bad_channels', 'length_ica_data', 'total_ICs', 'ICs_removed', 'total_epochs_before_artifact_rejection', ...
                    'total_epochs_after_artifact_rejection', 'total_channels_interpolated', 'any_usable_data'};
                writetable(report_table, [output_report_path '.csv'], "WriteMode", "append");
                continue % ignore rest of the processing and go to next datafile
            end
            
            %% STEP 12: Segment data into fixed length epochs
            %run event labeling script
            EEG = edit_event_markers_thrive(EEG);
            
            if epoch_data==1
                if task_eeg ==1 % task eeg
                    EEG = eeg_checkset(EEG);
                    EEG = pop_epoch(EEG, task_event_markers, task_epoch_length, 'epochinfo', 'yes');
                elseif task_eeg==0 % resting eeg
                    if overlap_epoch==1
                        EEG=eeg_regepochs(EEG,'recurrence',(rest_epoch_length/2),'limits',[0 rest_epoch_length], 'rmbase', [NaN], 'eventtype', char(dummy_events));
                        EEG = eeg_checkset(EEG);
                    else
                        EEG=eeg_regepochs(EEG,'recurrence',rest_epoch_length,'limits',[0 rest_epoch_length], 'rmbase', [NaN], 'eventtype', char(dummy_events));
                        EEG = eeg_checkset(EEG);
                    end
                end
            end
            
            total_epochs_before_artifact_rejection=EEG.trials;
            
            %% STEP 13: Remove baseline
            if remove_baseline==1
                EEG = eeg_checkset( EEG );
                EEG = pop_rmbase( EEG, baseline_window);
            end
            
            %% STEP 14: Artifact rejection
            all_bad_epochs=0;
            if voltthres_rejection==1 % check voltage threshold rejection
                if interp_epoch==1 % check epoch level channel interpolation
                    chans=[]; chansidx=[];chans_labels2=[];
                    chans_labels2=cell(1,EEG.nbchan);
                    for i=1:EEG.nbchan
                        chans_labels2{i}= EEG.chanlocs(i).labels;
                    end
                    [chans,chansidx] = ismember(frontal_channels, chans_labels2);
                    frontal_channels_idx = chansidx(chansidx ~= 0);
                    badChans = zeros(EEG.nbchan, EEG.trials);
                    badepoch=zeros(1, EEG.trials);
                    if isempty(frontal_channels_idx)==1 % check whether there is any frontal channel in dataset to check
                        warning('No frontal channels from the list present in the data. Only epoch interpolation will be performed.');
                    else
                        % find artifaceted epochs by detecting outlier voltage in the specified channels list and remove epoch if artifacted in those channels
                        for ch =1:length(frontal_channels_idx)
                            EEG = pop_eegthresh(EEG,1, frontal_channels_idx(ch), volt_threshold(1), volt_threshold(2), EEG.xmin, EEG.xmax,0,0);
                            EEG = eeg_checkset( EEG );
                            EEG = eeg_rejsuperpose( EEG, 1, 1, 1, 1, 1, 1, 1, 1);
                            badChans(ch,:) = EEG.reject.rejglobal;
                        end
                        for ii=1:size(badChans, 2)
                            badepoch(ii)=sum(badChans(:,ii));
                        end
                        badepoch=logical(badepoch);
                    end
                    
                    % If all epochs are artifacted, save the dataset and ignore rest of the preprocessing for this subject.
                    if sum(badepoch)==EEG.trials || sum(badepoch)+1==EEG.trials
                        all_bad_epochs=1;
                        warning(['No usable data for datafile', datafile_names{subject}]);
                        if output_format==1
                            EEG = eeg_checkset(EEG);
                            EEG = pop_editset(EEG, 'setname',  strcat(subj,'_',task,'_no_usable_data_all_bad_epochs_',sess,desc));
                            EEG = pop_saveset(EEG, 'filename', strcat(subj,'_',task,'_no_usable_data_all_bad_epochs_',sess,desc,'.set'),'filepath', [output_location filesep ]); % save .set format
                        elseif output_format==2
                            parsave([[output_location filesep ] strcat(subj,'_',task,'_no_usable_data_all_bad_epochs_',sess,desc,'.mat')], EEG); % save .mat format
                        end
                    else
                        EEG = pop_rejepoch( EEG, badepoch, 0);
                        EEG = eeg_checkset(EEG);
                    end
                    
                    if all_bad_epochs==1
                        warning(['No usable data for datafile', datafile_names{subject}]);
                    else
                        % Interpolate artifacted data for all reaming channels
                        badChans = zeros(EEG.nbchan, EEG.trials);
                        % Find artifacted epochs by detecting outlier voltage but don't remove
                        for ch=1:EEG.nbchan
                            EEG = pop_eegthresh(EEG,1, ch, volt_threshold(1), volt_threshold(2), EEG.xmin, EEG.xmax,0,0);
                            EEG = eeg_checkset(EEG);
                            EEG = eeg_rejsuperpose(EEG, 1, 1, 1, 1, 1, 1, 1, 1);
                            badChans(ch,:) = EEG.reject.rejglobal;
                        end
                        tmpData = zeros(EEG.nbchan, EEG.pnts, EEG.trials);
                        for e = 1:EEG.trials
                            % Initialize variables EEGe and EEGe_interp;
                            EEGe = []; EEGe_interp = []; badChanNum = [];
                            % Select only this epoch (e)
                            EEGe = pop_selectevent( EEG, 'epoch', e, 'deleteevents', 'off', 'deleteepochs', 'on', 'invertepochs', 'off');
                            badChanNum = find(badChans(:,e)==1); % find which channels are bad for this epoch
                            EEGe_interp = eeg_interp(EEGe,badChanNum); %interpolate the bad channels for this epoch
                            tmpData(:,:,e) = EEGe_interp.data; % store interpolated data into matrix
                        end
                        EEG.data = tmpData; % now that all of the epochs have been interpolated, write the data back to the main file
                        
                        % If more than 10% of channels in an epoch were interpolated, reject that epoch
                        badepoch=zeros(1, EEG.trials);
                        for ei=1:EEG.trials
                            NumbadChan = badChans(:,ei); % find how many channels are bad in an epoch
                            if sum(NumbadChan) > round((10/100)*EEG.nbchan)% check if more than 10% are bad
                                badepoch (ei)= sum(NumbadChan);
                            end
                        end
                        badepoch=logical(badepoch);
                    end
                    % If all epochs are artifacted, save the dataset and ignore rest of the preprocessing for this subject.
                    if sum(badepoch)==EEG.trials || sum(badepoch)+1==EEG.trials
                        all_bad_epochs=1;
                        warning(['No usable data for datafile', datafile_names{subject}]);
                        if output_format==1
                            EEG = eeg_checkset(EEG);
                            EEG = pop_editset(EEG, 'setname',  strcat(subj,'_',task,'_no_usable_data_all_bad_epochs_',sess,desc));
                            EEG = pop_saveset(EEG, 'filename', strcat(subj,'_',task,'_no_usable_data_all_bad_epochs_',sess,desc,'.set'),'filepath', [output_location filesep ]); % save .set format
                        elseif output_format==2
                            parsave([[output_location filesep ] strcat(subj,'_',task,'_no_usable_data_all_bad_epochs_',sess,desc,'.mat')], EEG); % save .mat format
                        end
                    else
                        EEG = pop_rejepoch(EEG, badepoch, 0);
                        EEG = eeg_checkset(EEG);
                    end
                else % if no epoch level channel interpolation
                    EEG = pop_eegthresh(EEG, 1, (1:EEG.nbchan), volt_threshold(1), volt_threshold(2), EEG.xmin, EEG.xmax, 0, 0);
                    EEG = eeg_checkset(EEG);
                    EEG = eeg_rejsuperpose( EEG, 1, 1, 1, 1, 1, 1, 1, 1);
                end % end of epoch level channel interpolation if statement
                
                % If all epochs are artifacted, save the dataset and ignore rest of the preprocessing for this subject.
                if sum(EEG.reject.rejthresh)==EEG.trials || sum(EEG.reject.rejthresh)+1==EEG.trials
                    all_bad_epochs=1;
                    warning(['No usable data for datafile', datafile_names{subject}]);
                    if output_format==1
                        EEG = eeg_checkset(EEG);
                        EEG = pop_editset(EEG, 'setname',  strcat(subj,'_',task,'_no_usable_data_all_bad_epochs_',sess,desc));
                        EEG = pop_saveset(EEG, 'filename', strcat(subj,'_',task,'_no_usable_data_all_bad_epochs_',sess,desc,'.set'),'filepath', [output_location filesep ]); % save .set format
                    elseif output_format==2
                        parsave([[output_location filesep ] strcat(subj,'_',task,'_no_usable_data_all_bad_epochs_',sess,desc,'.mat')], EEG); % save .mat format
                    end
                else
                    EEG = pop_rejepoch(EEG,(EEG.reject.rejthresh), 0);
                    EEG = eeg_checkset(EEG);
                end
            end % end of voltage threshold rejection if statement
            
            
            %     %save data here for training purposes only (usually do not save here)
            %     %only doing this to allow for skipping the full run of ica
            %     EEG = pop_saveset(EEG, 'filename', strrep(datafile_names{subject}, ext, '_processed_data_immediate.set'),'filepath', [output_location filesep 'processed_data' filesep ]); % save .set format
            %     %load data here for training purposes only (usually do not save here)
            %     %only doing this to allow for skipping the full run of ica
            %     EEG = pop_loadset( 'filename', strrep(datafile_names{subject}, ext, '_processed_data_immediate.set'), 'filepath', [output_location filesep 'processed_data' filesep]);
            
            
            
            
            % if all epochs are found bad during artifact rejection
            if all_bad_epochs==1
                total_epochs_after_artifact_rejection=0;
                total_channels_interpolated=0;
                any_usable_data = 0;
                report_table=table({datafile_names{subject}}, {datetime('now')}, {reference_used_for_faster}, {faster_bad_channels}, {ica_preparation_bad_channels}, {length_ica_data}, ...
                    {total_ICs}, {ICs_removed}, {total_epochs_before_artifact_rejection}, {total_epochs_after_artifact_rejection}, {total_channels_interpolated}, {any_usable_data});
                report_table.Properties.VariableNames={'datafile_names', 'date_processed', 'reference_used_for_faster', 'faster_bad_channels', ...
                    'ica_preparation_bad_channels', 'length_ica_data', 'total_ICs', 'ICs_removed', 'total_epochs_before_artifact_rejection', ...
                    'total_epochs_after_artifact_rejection', 'total_channels_interpolated', 'any_usable_data'};
                writetable(report_table, [output_report_path '.csv'], "WriteMode", "append");
                continue % ignore rest of the processing and go to next datafile
            else
                total_epochs_after_artifact_rejection=EEG.trials;
            end
            
            %% STEP 15: Interpolate deleted channels
            if interp_channels==1
                EEG = eeg_interp(EEG, channels_analysed);
                EEG = eeg_checkset(EEG);
            end
            if numel(FASTbadChans)==0 && numel(ica_prep_badChans)==0
                total_channels_interpolated=0;
            else
                total_channels_interpolated=numel(FASTbadChans)+ numel(ica_prep_badChans);
            end
            
            %% STEP 16: Parallel rereferencing
            if rerefer_data==1
                if iscell(reref)
                    reref_idx = zeros(1, length(reref));
                    for rr=1:length(reref)
                        reref_idx(rr) = find(strcmp({EEG.chanlocs.labels}, reref{rr}));
                    end
                    EEG = parallel_reref(EEG, reref_idx);
                else
                    EEG = parallel_reref(EEG, reref);
                end
                EEG = eeg_checkset(EEG);
            end
            
            %% Save processed data
            if output_format==1
                EEG = eeg_checkset(EEG);
                EEG = pop_editset(EEG, 'setname',  strcat(subj,'_',task,'_processed_data_',sess,desc));
                EEG = pop_saveset(EEG, 'filename', strcat(subj,'_',task,'_processed_data_',sess,desc,'.set'),'filepath', [output_location filesep ]); % save .set format
            elseif output_format==2
                parsave([[output_location filesep ] strcat(subj,'_',task,'_processed_data_',sess,desc,'.mat')], EEG); % save .mat format
            end
            
            
            
            filtered_filename = [[output_location filesep ] strcat(subj,'_',task,'_filtered_data_',sess,desc)];
            ica_filename = [[output_location filesep ] strcat(subj,'_',task,'_ica_data_',sess,desc)];
            processed_filename = [[output_location filesep ] strcat(subj,'_',task,'_processed_data_',sess,desc)];
            
            if save_interim_result
                if output_format==1
                    if ~isfile([ filtered_filename '.set' ]) | ~isfile([ ica_filename '.set' ]) | ~isfile([ processed_filename '.set' ])
                        error(['Error: Not all expected output files ' filtered_filename '.set, ' ica_filename '.set, ' processed_filename '.set were outputted, exiting.'])
                    end
                elseif output_format==2
                    if ~isfile([ filtered_filename '.mat' ]) | ~isfile([ ica_filename '.mat' ]) | ~isfile([ processed_filename '.mat' ])
                        error(['Error: Not all expected output files ' filtered_filename '.mat, ' ica_filename '.mat, ' processed_filename '.mat were outputted, exiting.'])
                    end
                end
            else
                if output_format==1
                    if ~isfile([ processed_filename '.set' ])
                        error(['Error: Not all expected output files ' processed_filename '.set were outputted, exiting.'])
                    end
                elseif output_format==2
                    if ~isfile([ processed_filename '.mat' ])
                        error(['Error: Not all expected output files ' processed_filename '.mat were outputted, exiting.'])
                    end
                end
            end
            
            
            %% create, write/append table on each iteration of loop
            
            %Create the report table for all the data files with relevant preprocessing outputs.
            any_usable_data = 1;
            report_table=table({datafile_names{subject}}, {datetime('now')}, {reference_used_for_faster}, {faster_bad_channels}, {ica_preparation_bad_channels}, {length_ica_data}, ...
                {total_ICs}, {ICs_removed}, {total_epochs_before_artifact_rejection}, {total_epochs_after_artifact_rejection}, {total_channels_interpolated}, {any_usable_data});
            
            report_table.Properties.VariableNames={'datafile_names', 'date_processed', 'reference_used_for_faster', 'faster_bad_channels', ...
                'ica_preparation_bad_channels', 'length_ica_data', 'total_ICs', 'ICs_removed', 'total_epochs_before_artifact_rejection', ...
                'total_epochs_after_artifact_rejection', 'total_channels_interpolated', 'any_usable_data'};
            
            %write/append table to disk
            writetable(report_table, [output_report_path '.csv'], "WriteMode", "append");
            % final_report_table = vertcat(final_report_table, report_table);
            
        end % end of subject loop
        
        delete(gcp); % Clean up parallel pool
        
        
        %writetable(final_report_table, [output_location filesep 'MADE_preprocessing_report.csv']);
        subjEnd = toc(subjStart);
        fprintf('MADE pipeline completed for subject %s in %d hours %.3f minutes, continuing.\n', subjects_to_process(file_locater_counter), floor(subjEnd/3600), rem(subjEnd,3600)/60);
        diary off
        
        
        
        
    catch
        fprintf('ERROR: failed for subject %s, look at log in %s/MADE_logfiles for details, continuing.\n', subjects_to_process(file_locater_counter), output_location);
        any_usable_data = 0;
        report_table=table({datafile_names{subject}}, {datetime('now')}, {reference_used_for_faster}, {faster_bad_channels}, {ica_preparation_bad_channels}, {length_ica_data}, ...
            {total_ICs}, {ICs_removed}, {total_epochs_before_artifact_rejection}, {total_epochs_after_artifact_rejection}, {total_channels_interpolated}, {any_usable_data});
        report_table.Properties.VariableNames={'datafile_names', 'date_processed', 'reference_used_for_faster', 'faster_bad_channels', ...
            'ica_preparation_bad_channels', 'length_ica_data', 'total_ICs', 'ICs_removed', 'total_epochs_before_artifact_rejection', ...
            'total_epochs_after_artifact_rejection', 'total_channels_interpolated', 'any_usable_data'};
        writetable(report_table, [output_report_path '_ERROR_incomplete.csv'], "WriteMode", "append");
    end
    
    
end



end

function [] = parsave(file, x)
save(file, 'x')
end

function filteredData = parallel_pop_firws(data, filterParams, srate)
% Wrapper function to call pop_firws on a specific data segment
% data: the data segment to filter (e.g., a single channel of EEG data)
% filterParams: cell array containing filter parameters for pop_firws
% srate: sampling rate of the EEG data, required by pop_firws

% Create a temporary EEG structure with necessary fields
EEGtemp = eeg_emptyset;          % Initialize an empty EEG structure
EEGtemp.data = data;              % Insert the data segment
EEGtemp.srate = srate;            % Set the sampling rate
EEGtemp.nbchan = size(data, 1);   % Set number of channels (usually 1 for single-channel processing)
EEGtemp.pnts = size(data, 2);     % Set number of points (time samples)
EEGtemp.trials = 1;               % Set number of trials (1 if continuous data)

% Call pop_firws on the temporary EEG structure
EEGtemp = pop_firws(EEGtemp, filterParams{:});

% Extract the filtered data
filteredData = EEGtemp.data;
end


% function [] = writeoutcsv(outpath)
%     report_table=table({datafile_names{subject}}, {datetime('now')}, {reference_used_for_faster}, {faster_bad_channels}, {ica_preparation_bad_channels}, {length_ica_data}, ...
%         {total_ICs}, {ICs_removed}, {total_epochs_before_artifact_rejection}, {total_epochs_after_artifact_rejection}, {total_channels_interpolated});
%     report_table.Properties.VariableNames={'datafile_names', 'date_processed', 'reference_used_for_faster', 'faster_bad_channels', ...
%         'ica_preparation_bad_channels', 'length_ica_data', 'total_ICs', 'ICs_removed', 'total_epochs_before_artifact_rejection', ...
%         'total_epochs_after_artifact_rejection', 'total_channels_interpolated'};
%     writetable(report_table, [output_location filesep 'MADE_preprocessing_report_' task '.csv'], "WriteMode", "append");
% end

% function [] = writeoutcsv(outpath)
%     report_table=table({datafile_names{subject}}, {datetime('now')}, {reference_used_for_faster}, {faster_bad_channels}, {ica_preparation_bad_channels}, {length_ica_data}, ...
%         {total_ICs}, {ICs_removed}, {total_epochs_before_artifact_rejection}, {total_epochs_after_artifact_rejection}, {total_channels_interpolated});
%     report_table.Properties.VariableNames={'datafile_names', 'date_processed', 'reference_used_for_faster', 'faster_bad_channels', ...
%         'ica_preparation_bad_channels', 'length_ica_data', 'total_ICs', 'ICs_removed', 'total_epochs_before_artifact_rejection', ...
%         'total_epochs_after_artifact_rejection', 'total_channels_interpolated'};
%     writetable(report_table, [output_location filesep 'MADE_preprocessing_report_' task '.csv'], "WriteMode", "append");
% end

function filteredData = parallel_filter_channels(data, srate, filterCoeffs)
    % Parallel filtering of EEG channels
    % data: raw EEG data (channels x timepoints)
    % srate: sampling rate
    % filterCoeffs: pre-computed filter coefficients
    
    filteredData = zeros(size(data));
    parfor chanIdx = 1:size(data,1)
        filteredData(chanIdx, :) = filtfilt(filterCoeffs, 1, double(data(chanIdx, :)));
    end
end

function epochedData = parallel_create_epochs(data, srate, epochLength)
    % Create fixed-length epochs in parallel
    % data: continuous EEG data
    % srate: sampling rate
    % epochLength: length of each epoch in seconds
    
    epochSamples = epochLength * srate;
    numEpochs = floor(size(data, 2) / epochSamples);
    
    epochedData = zeros(size(data,1), epochSamples, numEpochs);
    parfor epochIdx = 1:numEpochs
        startIdx = (epochIdx-1)*epochSamples + 1;
        endIdx = startIdx + epochSamples - 1;
        epochedData(:,:,epochIdx) = data(:,startIdx:endIdx);
    end
end

function [badChans, tmpData] = parallel_artifact_detection(EEG, volt_threshold)
    % Parallel artifact detection and interpolation across channels/epochs
    % EEG: EEG structure
    % volt_threshold: voltage threshold for artifact detection
    
    % Initialize variables
    badChans = zeros(EEG.nbchan, EEG.trials);
    
    % Parallel artifact detection across channels
    parfor ch = 1:EEG.nbchan
        tmpEEG = pop_eegthresh(EEG, 1, ch, volt_threshold(1), volt_threshold(2), ...
            EEG.xmin, EEG.xmax, 0, 0);
        tmpEEG = eeg_rejsuperpose(tmpEEG, 1, 1, 1, 1, 1, 1, 1);
        badChans(ch,:) = tmpEEG.reject.rejglobal;
    end
    
    % Parallel epoch interpolation
    tmpData = zeros(EEG.nbchan, EEG.pnts, EEG.trials);
    parfor e = 1:EEG.trials
        tmpData(:,:,e) = interpolate_epoch(EEG.data(:,:,e), badChans(:,e), ...
            EEG.nbchan, EEG.chanlocs);
    end
end

function epochData = interpolate_epoch(data, badChanMask, nbchan, chanlocs)
    % Helper function to interpolate bad channels in a single epoch
    badChanIdx = find(badChanMask==1);
    
    if ~isempty(badChanIdx)
        % Create temporary EEG structure for interpolation
        tmpEEG = eeg_emptyset();
        tmpEEG.data = data;
        tmpEEG.nbchan = nbchan;
        tmpEEG.chanlocs = chanlocs;
        
        % Interpolate bad channels
        tmpEEG = eeg_interp(tmpEEG, badChanIdx);
        epochData = tmpEEG.data;
    else
        epochData = data;
    end
end

function interpData = parallel_channel_interpolation(EEG, channels_analysed, N_CPUS)
    % Parallel channel interpolation across channel groups
    % Split channels into groups for parallel processing
    chunkSize = ceil(EEG.nbchan / N_CPUS);
    chanGroups = arrayfun(@(x) (x:min(x+chunkSize-1,EEG.nbchan)), ...
        1:chunkSize:EEG.nbchan, 'UniformOutput', false);
    
    % Parallel interpolation
    interpData = cell(length(chanGroups), 1);
    parfor groupIdx = 1:length(chanGroups)
        chanIdx = chanGroups{groupIdx};
        tmpEEG = eeg_emptyset();
        tmpEEG.data = EEG.data(chanIdx,:,:);
        tmpEEG.nbchan = length(chanIdx);
        tmpEEG.chanlocs = EEG.chanlocs(chanIdx);
        
        % Interpolate channels in this group
        tmpEEG = eeg_interp(tmpEEG, channels_analysed(ismember(channels_analysed, chanIdx)));
        interpData{groupIdx} = tmpEEG.data;
    end
    
    % Combine interpolated data
    interpData = cat(1, interpData{:});
end

%% Add these new parallel processing functions at the bottom of the file:

function EEG = parallel_runica(EEG, N_CPUS)
    % Parallel ICA computation by splitting data into temporal chunks
    % Each worker processes a subset of the data
    
    % Split data into temporal chunks
    chunkSize = floor(EEG.pnts / N_CPUS);
    chunks = cell(N_CPUS, 1);
    
    % Process chunks in parallel
    parfor i = 1:N_CPUS
        startIdx = (i-1)*chunkSize + 1;
        endIdx = min(i*chunkSize, EEG.pnts);
        
        % Create temporary EEG structure for this chunk
        tmpEEG = eeg_emptyset();
        tmpEEG.data = EEG.data(:, startIdx:endIdx, :);
        tmpEEG.srate = EEG.srate;
        tmpEEG.nbchan = EEG.nbchan;
        tmpEEG.trials = EEG.trials;
        
        % Run ICA on this chunk
        tmpEEG = pop_runica(tmpEEG, 'icatype', 'runica', 'extended', 1, 'stop', 1E-7, 'interupt','off');
        chunks{i} = tmpEEG;
    end
    
    % Combine ICA results
    EEG.icaweights = mean(cat(3, chunks{:}.icaweights), 3);
    EEG.icasphere = mean(cat(3, chunks{:}.icasphere), 3);
    EEG = eeg_checkset(EEG);
end

function [EEG, badEpochs] = parallel_reject_artifacts(EEG, volt_threshold, emg_thrs, emg_freqs_limit)
    % Parallel artifact rejection across epochs
    % Returns modified EEG and indices of bad epochs
    
    numEpochs = EEG.trials;
    badEpochs = false(1, numEpochs);
    
    % Process epochs in parallel
    parfor epochIdx = 1:numEpochs
        % Extract single epoch
        epochData = EEG.data(:,:,epochIdx);
        
        % Check voltage threshold
        if any(any(epochData < volt_threshold(1) | epochData > volt_threshold(2)))
            badEpochs(epochIdx) = true;
            continue;
        end
        
        % Check EMG (muscle) artifacts using FFT
        [spectra, freqs] = spectopo(epochData, 0, EEG.srate, 'plot', 'off');
        freqMask = freqs >= emg_freqs_limit(1) & freqs <= emg_freqs_limit(2);
        if any(spectra(:,freqMask) < emg_thrs(1) | spectra(:,freqMask) > emg_thrs(2))
            badEpochs(epochIdx) = true;
        end
    end
    
    % Remove bad epochs
    EEG = pop_select(EEG, 'notrial', find(badEpochs));
end

function EEG = parallel_reref(EEG, reref)
    % Parallel rereferencing of channels
    % reref can be channel indices or empty for average reference
    
    if isempty(reref)
        % Average reference
        parfor chanIdx = 1:EEG.nbchan
            EEG.data(chanIdx,:,:) = EEG.data(chanIdx,:,:) - mean(EEG.data,1);
        end
    else
        % Specific reference channels
        refData = mean(EEG.data(reref,:,:),1);
        parfor chanIdx = 1:EEG.nbchan
            EEG.data(chanIdx,:,:) = EEG.data(chanIdx,:,:) - refData;
        end
    end
end
