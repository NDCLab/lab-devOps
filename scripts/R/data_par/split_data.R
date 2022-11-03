myargs <- commandArgs(trailingOnly=TRUE)
d_name <- myargs[2]
nodes <- as.integer(myargs[1])

data <- read.csv(d_name, header=TRUE, stringsAsFactors=FALSE)

# get uniq values and mode
uniq_vals <- as.list(unique(data$subject))
subs_in_chunk <- ceiling(length(uniq_vals)/nodes)
sub_count <- 0
orig_subs <- subs_in_chunk

# loop through nodes and create
for (x in 1:nodes) {
    full_chunk <- data.frame()
    while (sub_count < subs_in_chunk) {
        chunk <- data[data$subject == uniq_vals[sub_count],]
        full_chunk <- rbind(full_chunk, chunk)
        sub_count <- sub_count + 1
    }

    colnames(full_chunk) <- colnames(data)

    write.csv(full_chunk, paste(d_name, "chunk", x, sep = "_", collapse = NULL), row.names=FALSE)
    subs_in_chunk <- subs_in_chunk + orig_subs
}
