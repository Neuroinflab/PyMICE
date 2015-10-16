COMPRESSOR = zip -9
IC = IntelliCage/
NAME = icp3_data.zip

all: ${NAME}
	echo $@

${NAME}: Animals.txt DataDescriptor.xml Groups.txt Sessions.xml ${IC}Environment.txt ${IC}IntegerReporters.txt ${IC}Log.txt ${IC}Nosepokes.txt ${IC}Visits.txt
	${COMPRESSOR} $@ $?

clean:
	rm ${NAME}
