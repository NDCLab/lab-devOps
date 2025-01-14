function [] = parallelExample()

cluster = parcluster('local');
workersAvailable = maxNumCompThreads; % This should match the number of workers specified in the slurm .sub file
fprintf('%d workers available\n', workersAvailable)
parpool(cluster, workersAvailable) % starts the parpool

lenSubjectsToProcess=16;

parfor i = 1:lenSubjectsToProcess
    fprintf('Processing subject #%d\n', i)
    pause(30)
    fprintf('Processing for #%d complete\n', i)
end

fprintf('Parallel processing complete')

end
