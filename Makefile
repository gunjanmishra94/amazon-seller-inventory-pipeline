IMAGE_NAME := oos-fabric-demo:latest

.PHONY: build run shell clean

build:
	docker build -t $(IMAGE_NAME) -f Dockerfile .

run: build
	docker run --rm \
		-v "$(CURDIR):/home/gunjan/work" \
		-w /home/gunjan/work \
		$(IMAGE_NAME) \
		python src/pipeline.py

shell: build
	docker run --rm -it \
		-v "$(CURDIR):/home/gunjan/work" \
		-w /home/gunjan/work \
		$(IMAGE_NAME) \
		bash

clean:
	rm -rf lakehouse output
