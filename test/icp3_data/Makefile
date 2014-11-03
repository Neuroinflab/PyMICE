COMPRESSOR = zip -9
IC = IntelliCage/

all: icp3_data.zip
	echo $@

icp3_data.zip: Animals.txt DataDescriptor.xml Groups.txt Sessions.xml ${IC}Environment.txt ${IC}IntegerReporters.txt ${IC}Log.txt ${IC}Nosepokes.txt ${IC}Visits.txt
	${COMPRESSOR} $@ $?

clean:
	rm icp3_data.zip
