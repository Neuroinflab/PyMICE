COMPRESSOR = zip -9
IC = IntelliCage/
ALL = legacy_data.zip legacy_data_nosubdir.zip
SOURCES = Animals.txt ${IC}DataDescriptor.xml ${IC}Environment.txt ${IC}Groups.txt ${IC}HardwareEvents.txt ${IC}Log.txt ${IC}Motions.txt ${IC}Nosepokes.txt ${IC}Sessions.xml ${IC}Visits.txt

all: ${ALL}
	echo $@

${ALL}: ${SOURCES}

legacy_data.zip:
	${COMPRESSOR} $@ ${SOURCES}

legacy_data_nosubdir.zip:
	${COMPRESSOR} -j $@ ${SOURCES}

clean:
	rm ${ALL}
