docker image build -t baangt-pdf-comparison .
docker run --rm -ti -p 5050:5000 --name baangtPDFComparison baangt-pdf-comparison:latest
