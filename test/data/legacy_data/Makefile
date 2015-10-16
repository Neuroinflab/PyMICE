COMPRESSOR = zip -9
IC = IntelliCage/
NAME = legacy_data.zip

all: ${NAME}
	echo $@

${NAME}: Animals.txt ${IC}DataDescriptor.xml ${IC}Environment.txt ${IC}Groups.txt ${IC}HardwareEvents.txt ${IC}Log.txt ${IC}Motions.txt ${IC}Nosepokes.txt ${IC}Sessions.xml ${IC}Visits.txt
	${COMPRESSOR} $@ $?

clean:
	rm ${NAME}
