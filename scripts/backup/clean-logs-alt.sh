#!/bin/bash
# A script to clean up log files if they surpass a size. Will be run automatically via cron.

# USAGE: bash /home/data/NDClab/tools/lab-devOps/scripts/backup/clean-logs.sh -r -d MM_YYYY-MM_YYYY

usage() {
  cat <<EOF
  Usage: $0 [-r] [-d MM_YYYY-MM_YYYY]

  -r record log sizes for each month
  -d mark logs from MM_YYYY to MM_YYYY for deletion in a "to_be_deleted.txt" file

EOF
exit 0
}

if [ $# -eq 0 ]; then usage; exit 1; fi

while getopts "d:r" opt; do
  case "${opt}" in
    d) # mark logs from MM_YYYY to MM_YYYY for deletion
      d=${OPTARG}
      START_DATE=$(echo $d | cut -d "-" -f1)
      END_DATE=$(echo $d | cut -d "-" -f2)
      ;;
    r) # record log sizes for each month
      record_logs=true
      ;;
    \?)
      echo "not expected flag"; usage
      ;;
  esac
done

if [[ ! $START_DATE == "" ]]; then
  start_month=${START_DATE:0:2}
  start_year=${START_DATE:3:4}
  end_month=${END_DATE:0:2}
  end_year=${END_DATE:3:4}
  if [[ $end_year -lt $start_year || ($end_year -eq $start_year && 10#$end_month -lt 10#$start_month) ]]
    then
      echo "Start date must be before end date, in \"MM_YYYY\" format."; exit 1
  fi
  
  # create array of dates to match with log dates
  if [[ $end_year -eq $start_year ]]; then
    for month in $(seq -w $start_month $end_month)
      do
        log_dates_arr+=("$month"_"$end_year")
      done
  else
    for month in $(seq -w $start_month 12); do
      log_dates_arr+=("$month"_"$start_year")
    done
    year=$(( $start_year + 1 ))
    while [[ $year -lt $end_year ]]; do
      for month in {00..12}; do log_dates_arr+=("$month"_"$year"); done
      ((year++))
    done
    for month in $(seq -w 01 $end_month); do
      log_dates_arr+=("$month"_"$end_year")
    done
  fi

  # create "to_be_deleted.txt" file
  echo "creating \"to_be_deleted.txt\" of log files from $start_month $start_year to $end_month $end_year"
  purge_this="to_be_deleted.txt"
  for date in ${log_dates_arr[@]}; do
    find . -regextype posix-extended -regex ".*"${date:0:2}"_[0-9]{2}_"${date:3:4}"\:\:[0-9]{2}\:[0-9]{2}\:[0-9]{2}\.log$" -exec echo {} >> $purge_this \;
  done
fi


# Keep track of how much space logs from each month are taking up
if [[ $record_logs == true ]]; then
  months=(January February March April May June July August September October November December)
  month_number=(01 02 03 04 05 06 07 08 09 10 11 12)

  for year in {2020..2023}
  do
    ii=0
    for month in ${month_number[@]}
    do
      log_size=$(find . -regextype posix-extended -regex ".*"${month}"_[0-9]{2}_"$year"\:\:[0-9]{2}\:[0-9]{2}\:[0-9]{2}\.log$" -exec du -cshk {} + | grep total | awk '{print $1}')
      if [[ ! $log_size == "" ]]; then
        echo "The logs from ${months[$ii]} ${year} take up ${log_size} KB."
      fi
      ((ii++))
    done
  done
fi
