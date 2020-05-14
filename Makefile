###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2014-2017 Jakub M. Dzik a.k.a. Kowalski (Laboratory of     #
#    Neuroinformatics; Nencki Institute of Experimental Biology of Polish     #
#    Academy of Sciences)                                                     #
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

TEST_DIR  = test/data/
LDATA_DIR = ${TEST_DIR}legacy_data/
LDATA_IC_DIR = ${LDATA_DIR}IntelliCage/
ICP3DATA_DIR = ${TEST_DIR}icp3_data/
ICP3DATA_IC_DIR = ${ICP3DATA_DIR}IntelliCage/
ICP31DATA_DIR = ${TEST_DIR}icp31_data/
ICP31DATA_IC_DIR = ${ICP31DATA_DIR}IntelliCage/
EDATA_DIR = ${TEST_DIR}empty_data/
EDATA_IC_DIR = ${EDATA_DIR}IntelliCage/
MEDATA_DIR = ${TEST_DIR}more_empty_data/
MEDATA_IC_DIR = ${MEDATA_DIR}IntelliCage/
RETAGGEDDATA_DIR = ${TEST_DIR}retagged_data/
RETAGGEDDATA_IC_DIR = ${RETAGGEDDATA_DIR}IntelliCage/
VERSION2_2DATA_DIR = ${TEST_DIR}version2_2_data/
VERSION2_2DATA_IC_DIR =${VERSION2_2DATA_DIR}IntelliCage/
COMPRESSOR = zip -9 $@ $?


all: tests
	echo "Done"

tests: ${TEST_DIR}legacy_data.zip ${TEST_DIR}legacy_data_nosubdir.zip ${TEST_DIR}empty_data.zip ${TEST_DIR}more_empty_data.zip ${TEST_DIR}icp3_data.zip ${TEST_DIR}icp31_data.zip ${TEST_DIR}retagged_data.zip ${TEST_DIR}version2_2_data.zip ${TEST_DIR}version2_2_data_nosubdir.zip
	echo "Tests"

${TEST_DIR}legacy_data.zip: ${LDATA_DIR}legacy_data.zip
	cp $? $@

${TEST_DIR}legacy_data_nosubdir.zip: ${LDATA_DIR}legacy_data_nosubdir.zip
	cp $? $@

${TEST_DIR}icp3_data.zip: ${ICP3DATA_DIR}icp3_data.zip
	cp $? $@

${TEST_DIR}icp31_data.zip: ${ICP31DATA_DIR}icp31_data.zip
	cp $? $@

${TEST_DIR}empty_data.zip: ${EDATA_DIR}empty_data.zip
	cp $? $@

${TEST_DIR}more_empty_data.zip: ${MEDATA_DIR}more_empty_data.zip
	cp $? $@

${TEST_DIR}retagged_data.zip: ${RETAGGEDDATA_DIR}retagged_data.zip
	cp $? $@

${TEST_DIR}version2_2_data.zip: ${VERSION2_2DATA_DIR}version2_2_data.zip
	cp $? $@

${TEST_DIR}version2_2_data_nosubdir.zip: ${VERSION2_2DATA_DIR}version2_2_data_nosubdir.zip
	cp $? $@

${LDATA_DIR}legacy_data.zip ${LDATA_DIR}legacy_data_nosubdir.zip: ${LDATA_DIR}Animals.txt ${LDATA_IC_DIR}DataDescriptor.xml ${LDATA_IC_DIR}Environment.txt ${LDATA_IC_DIR}Groups.txt ${LDATA_IC_DIR}HardwareEvents.txt ${LDATA_IC_DIR}Log.txt ${LDATA_IC_DIR}Motions.txt ${LDATA_IC_DIR}Nosepokes.txt ${LDATA_IC_DIR}Sessions.xml ${LDATA_IC_DIR}Visits.txt

${ICP3DATA_DIR}icp3_data.zip: ${ICP3DATA_DIR}Animals.txt ${ICP3DATA_DIR}DataDescriptor.xml ${ICP3DATA_DIR}Groups.txt ${ICP3DATA_DIR}Sessions.xml ${ICP3DATA_IC_DIR}Environment.txt ${ICP3DATA_IC_DIR}HardwareEvents.txt ${ICP3DATA_IC_DIR}IntegerReporters.txt ${ICP3DATA_IC_DIR}Log.txt ${ICP3DATA_IC_DIR}Nosepokes.txt ${ICP3DATA_IC_DIR}Visits.txt

${ICP31DATA_DIR}icp31_data.zip: ${ICP31DATA_DIR}Animals.txt ${ICP31DATA_DIR}DataDescriptor.xml ${ICP31DATA_DIR}Groups.txt ${ICP31DATA_DIR}Sessions.xml ${ICP31DATA_IC_DIR}Environment.txt ${ICP31DATA_IC_DIR}HardwareEvents.txt ${ICP31DATA_IC_DIR}IntegerReporters.txt ${ICP31DATA_IC_DIR}Log.txt ${ICP31DATA_IC_DIR}Nosepokes.txt ${ICP31DATA_IC_DIR}Visits.txt

${EDATA_DIR}empty_data.zip: ${EDATA_DIR}Animals.txt ${EDATA_DIR}DataDescriptor.xml ${EDATA_DIR}Groups.txt ${EDATA_DIR}Sessions.xml ${EDATA_IC_DIR}Environment.txt ${EDATA_IC_DIR}IntegerReporters.txt ${EDATA_IC_DIR}Log.txt ${EDATA_IC_DIR}Nosepokes.txt ${EDATA_IC_DIR}Visits.txt

${MEDATA_DIR}more_empty_data.zip: ${MEDATA_DIR}Animals.txt ${MEDATA_DIR}DataDescriptor.xml ${MEDATA_DIR}Groups.txt ${MEDATA_DIR}Sessions.xml ${MEDATA_IC_DIR}Log.txt ${MEDATA_IC_DIR}Nosepokes.txt ${MEDATA_IC_DIR}Visits.txt

${RETAGGEDDATA_DIR}retagged_data.zip: ${RETAGGEDDATA_DIR}Animals.txt ${RETAGGEDDATA_DIR}DataDescriptor.xml ${RETAGGEDDATA_DIR}Groups.txt ${RETAGGEDDATA_DIR}Sessions.xml ${RETAGGEDDATA_IC_DIR}Environment.txt ${RETAGGEDDATA_IC_DIR}IntegerReporters.txt ${RETAGGEDDATA_IC_DIR}Log.txt ${RETAGGEDDATA_IC_DIR}Nosepokes.txt ${RETAGGEDDATA_IC_DIR}Visits.txt

${VERSION2_2DATA_DIR}version2_2_data.zip {VERSION2_2DATA_DIR}version2_2_data_nosubdir.zip: ${VERSION2_2DATA_DIR}Animals.txt ${VERSION2_2DATA_DIR}DataDescriptor.xml ${VERSION2_2DATA_DIR}Groups.txt ${VERSION2_2DATA_IC_DIR}Environment.txt  ${VERSION2_2DATA_IC_DIR}HardwareEvents.txt ${VERSION2_2DATA_IC_DIR}Log.txt ${VERSION2_2DATA_IC_DIR}Nosepokes.txt ${VERSION2_2DATA_IC_DIR}Sessions.xml ${VERSION2_2DATA_IC_DIR}Visits.txt

${LDATA_DIR}legacy_data.zip:
	make -C ${LDATA_DIR} legacy_data.zip

${LDATA_DIR}legacy_data_nosubdir.zip:
	make -C ${LDATA_DIR} legacy_data_nosubdir.zip

${ICP3DATA_DIR}icp3_data.zip:
	make -C ${ICP3DATA_DIR}

${ICP31DATA_DIR}icp31_data.zip:
	make -C ${ICP31DATA_DIR}

${EDATA_DIR}empty_data.zip:
	make -C ${EDATA_DIR}

${MEDATA_DIR}more_empty_data.zip:
	make -C ${MEDATA_DIR}

${RETAGGEDDATA_DIR}retagged_data.zip:
	make -C ${RETAGGEDDATA_DIR}

${VERSION2_2DATA_DIR}version2_2_data.zip:
	make -C ${VERSION2_2DATA_DIR} version2_2_data.zip

${VERSION2_2DATA_DIR}version2_2_data_nosubdir.zip:
	make -C ${VERSION2_2DATA_DIR} version2_2_data_nosubdir.zip

clean: clean_tests
	echo "Tests cleaned"

clean_tests:
	rm -rfv ${TEST_DIR}legacy_data.zip ${TEST_DIR}legacy_data_nosubdir.zip ${TEST_DIR}icp3_data.zip ${TEST_DIR}empty_data.zip ${TEST_DIR}more_empty_data.zip ${TEST_DIR}retagged_data.zip ${TEST_DIR}version2_2_data.zip
	make -C ${LDATA_DIR} clean
	make -C ${ICP3DATA_DIR} clean
	make -C ${ICP31DATA_DIR} clean
	make -C ${EDATA_DIR} clean
	make -C ${MEDATA_DIR} clean
	make -C ${RETAGGEDDATA_DIR} clean
	make -C ${VERSION2_2DATA_DIR} clean	
