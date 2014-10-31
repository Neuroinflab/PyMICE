COMPRESSOR = zip -9
IC = IntelliCage/


all: legacy_data.zip
	echo $@

legacy_data.zip: Animals.txt ${IC}DataDescriptor.xml ${IC}Environment.txt ${IC}Groups.txt ${IC}HardwareEvents.txt ${IC}Log.txt ${IC}Motions.txt ${IC}Nosepokes.txt ${IC}Sessions.xml ${IC}Visits.txt
	${COMPRESSOR} $@ $?

clean:
	rm legacy_data.zip
