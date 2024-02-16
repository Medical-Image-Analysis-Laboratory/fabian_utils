# Build from the MATLAB base image
FROM matlabwithtoolboxes:r2023b

# Copy your script/function to be executed.
COPY . /fabian

# Change directory
WORKDIR /fabian

# Install python dependencies
RUN pip install -r requirements_fabian.txt

ENV LD_LIBRARY_PATH="/opt/matlab/R2023b/bin/glnxa64"
