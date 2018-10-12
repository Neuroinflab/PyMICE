COMPRESSOR = zip -9
IC = IntelliCage/
ALL = version2_2_data.zip version2_2_data_nosubdir.zip
SOURCES = Animals.txt DataDescriptor.xml ${IC}Environment.txt Groups.txt ${IC}HardwareEvents.txt ${IC}Log.txt  ${IC}Nosepokes.txt ${IC}Sessions.xml ${IC}Visits.txt

all: ${ALL}
	echo $@

${ALL}: ${SOURCES}

version2_2_data.zip:
	${COMPRESSOR} $@ ${SOURCES}

version2_2_data_nosubdir.zip:
	${COMPRESSOR} -j $@ ${SOURCES}

clean:
	rm ${ALL}
