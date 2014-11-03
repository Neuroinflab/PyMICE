TEST_DIR  = test/
LDATA_DIR = ${TEST_DIR}legacy_data/
LDATA_IC_DIR = ${LDATA_DIR}IntelliCage/
ICP3DATA_DIR = ${TEST_DIR}icp3_data/
ICP3DATA_IC_DIR = ${ICP3DATA_DIR}IntelliCage/
EDATA_DIR = ${TEST_DIR}empty_data/
EDATA_IC_DIR = ${EDATA_DIR}IntelliCage/
COMPRESSOR = zip -9 $@ $?


all: tests
	echo "Done"

tests: ${TEST_DIR}icp3_data.zip ${TEST_DIR}legacy_data.zip ${TEST_DIR}empty_data.zip
	echo "Tests"

${TEST_DIR}legacy_data.zip: ${LDATA_DIR}legacy_data.zip
	cp $? $@

${TEST_DIR}icp3_data.zip: ${ICP3DATA_DIR}icp3_data.zip
	cp $? $@

${TEST_DIR}empty_data.zip: ${EDATA_DIR}empty_data.zip
	cp $? $@

${LDATA_DIR}legacy_data.zip: ${LDATA_DIR}Animals.txt ${LDATA_IC_DIR}DataDescriptor.xml ${LDATA_IC_DIR}Environment.txt ${LDATA_IC_DIR}Groups.txt ${LDATA_IC_DIR}HardwareEvents.txt ${LDATA_IC_DIR}Log.txt ${LDATA_IC_DIR}Motions.txt ${LDATA_IC_DIR}Nosepokes.txt ${LDATA_IC_DIR}Sessions.xml ${LDATA_IC_DIR}Visits.txt

${ICP3DATA_DIR}icp3_data.zip: ${ICP3DATA_DIR}Animals.txt ${ICP3DATA_DIR}DataDescriptor.xml ${ICP3DATA_DIR}Groups.txt ${ICP3DATA_DIR}Sessions.xml ${ICP3DATA_IC_DIR}Environment.txt ${ICP3DATA_IC_DIR}IntegerReporters.txt ${ICP3DATA_IC_DIR}Log.txt ${ICP3DATA_IC_DIR}Nosepokes.txt ${ICP3DATA_IC_DIR}Visits.txt

${EDATA_DIR}empty_data.zip: ${EDATA_DIR}Animals.txt ${EDATA_DIR}DataDescriptor.xml ${EDATA_DIR}Groups.txt ${EDATA_DIR}Sessions.xml ${EDATA_IC_DIR}Environment.txt ${EDATA_IC_DIR}IntegerReporters.txt ${EDATA_IC_DIR}Log.txt ${EDATA_IC_DIR}Nosepokes.txt ${EDATA_IC_DIR}Visits.txt

${LDATA_DIR}legacy_data.zip:
	make -C ${LDATA_DIR}

${ICP3DATA_DIR}icp3_data.zip:
	make -C ${ICP3DATA_DIR}

${EDATA_DIR}empty_data.zip:
	make -C ${EDATA_DIR}

clean: clean_tests
	echo "Tests cleaned"

clean_tests:
	rm -rfv ${TEST_DIR}legacy_data.zip ${TEST_DIR}icp3_data.zip ${TEST_DIR}empty_data.zip
	make -C ${LDATA_DIR} clean
	make -C ${ICP3DATA_DIR} clean
	make -C ${EDATA_DIR} clean
