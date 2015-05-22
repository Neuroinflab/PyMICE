#!/bin/bash
if [ $# -eq 0 ] || [ $# -gt 2 ]
then
  echo "Usage: $0 <session directory> [<archive directory>]"
  exit
fi

sessionDirectory="$1"

if [ $# -eq 2 ]
then
  archiveDirectory="$2"

else
  archiveDirectory="$sessionDirectory"

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
    }
    else
    {
      echo "WARNING: $archive missing"
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
