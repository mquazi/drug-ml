## Set up
### Docker
- Development
    - `docker build -t predictor-dev -f Dockerfile.dev .`
    - `docker run -p 5000:5000 -v `pwd`:/app predictor-dev`
- Production
    - `docker build -t predictor .`
    - `docker run -p 5000:5000 predictor`
    