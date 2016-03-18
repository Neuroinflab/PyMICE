COMPRESSOR = zip -9
IC = IntelliCage/
NAME = more_empty_data.zip

all: ${NAME}
	echo $@

${NAME}: Animals.txt DataDescriptor.xml Groups.txt Sessions.xml ${IC}Log.txt ${IC}Nosepokes.txt ${IC}Visits.txt
	${COMPRESSOR} $@ $?

clean:
	rm ${NAME}
