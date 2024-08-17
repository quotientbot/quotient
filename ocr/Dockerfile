FROM golang:1.22.6

RUN apt-get update -qq

RUN apt-get install -y -qq libtesseract-dev libleptonica-dev

ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata/

RUN apt-get install -y -qq \
    tesseract-ocr-eng

WORKDIR ${GOPATH}/src/quotient/ocr

COPY . .

RUN go get -v ./... && go install .

EXPOSE 8080

CMD ["ocr"]
