#!/bin/bash
if [ $# -eq 0 ] || [ $# -gt 3 ]
then
  echo "Usage: $0 <session directory> [<archive directory> [<destination directory>]]"
  exit
fi

sessionDirectory="$1"

if [ $# -gt 1 ]
then
  archiveDirectory="$2"

else
  archiveDirectory="$sessionDirectory"

fi

if [ $# -gt 2 ]
then
  destinationDirectory="$3"

else
  destinationDirectory="$archiveDirectory"

fi


for sessionPath in "$sessionDirectory/"[[:digit:]][[:digit:]][[:digit:]][[:digit:]]-[[:digit:]][[:digit:]]-[[:digit:]][[:digit:]]" "[[:digit:]][[:digit:]].[[:digit:]][[:digit:]].[[:digit:]][[:digit:]];
do
{
  if [ -d "$sessionPath" ]
  then
  {
    archive="$archiveDirectory/${sessionPath: -19}.zip"
    if [ -e "$archive" ]
    then
    {
      IFS=$'\n'
      for line in $(unzip -l "$archive" | tail -n +4 | head -n -2);
      do
      {
        IFS=$' '
        set $line
        if [ "$1" -ne "0" ]
        then
        {
          sessionFileName="$sessionPath/$4"
          if [ -e "$sessionFileName" ]
          then
          {
            sessionFileSize=`stat -c '%s'  "$sessionFileName"`
            if [ "$sessionFileSize" -ne "$1" ]
            then
              echo "WARNING: $sessionFileName differs in size ($1 != $sessionFileSize)"

            fi
          }
          else
          {
             echo "       : $sessionFileName missing"
          }
          fi
        }
        fi
      }
      done

      if [ "$archiveDirectory" != "$destinationDirectory" ]
      then
        ln -s "$archive" "$destinationDirectory"

      fi
    }
    else
    {
      echo "WARNING: $archive missing"
      wd=`pwd`
      cd "$sessionPath"
      zip `readlink -nf "$archive"` -9r *
      cd "$wd"
    }
    fi
  }
  else
  {
    printf 'ERROR  : path "%s" is not a directory!' "$sessionPath"
  }
  fi
}
done
