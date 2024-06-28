docker pull spikeinterface/kilosort4-base:latest

# figure out default user and home dir
# docker run --rm spikeinterface/kilosort4-base whoami
# root
# docker run --rm spikeinterface/kilosort4-base env | grep HOME
# /root

# Run local script inside the kilosort4 container.
docker run \
  --rm \
  --volume "$PWD":"/kilosort-test" \
  --volume "$HOME/.kilosort":"/root/.kilosort" \
  spikeinterface/kilosort4-base \
  python /kilosort-test/test_kilosort.py