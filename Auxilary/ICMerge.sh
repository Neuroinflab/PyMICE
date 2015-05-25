#!/bin/bash
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2015 Jakub M. Kowalski (Laboratory of Neuroinformatics;    #
#    Nencki Institute of Experimental Biology)                                #
#                                                                             #
#    This software is free software: you can redistribute it and/or modify    #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This software is distributed in the hope that it will be useful,         #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this software.  If not, see http://www.gnu.org/licenses/.     #
#                                                                             #
###############################################################################
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
