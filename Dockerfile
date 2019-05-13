FROM mbdevpl/usable-ubuntu:18.04

MAINTAINER Mateusz Bysiek <mateusz.bysiek.spam@gmail.com>

COPY . /home/user/software/transpyle

USER user
WORKDIR /home/user/software/transpyle

RUN \
  sudo apt-get update && \
  sudo apt-get install --no-install-recommends -y swig && \
  sudo apt-get clean && \
  sudo rm -rf /var/lib/apt/lists/* && \
  mkdir -p "/home/user/.local/bin" && \
  sudo chown -R user:user /home/user/software && \
  .build/install_open_fortran_compiler.sh && \
  .build/install_castxml.sh && \
  git clean -f -d -x && \
  python3 -m pip install --no-cache-dir --user timing && \
  python3 -m pip install --no-cache-dir --user -r requirements.txt && \
  python3 -m pip install --no-cache-dir --user .[all] && \
  echo "python3 -m transpyle --help" >> /home/user/.bash_history && \
  echo "python3 -m transpyle --langs" >> /home/user/.bash_history

# sudo python3 -m pip install --no-cache-dir -U pip && \
# .build/install_open_fortran_parser.sh && \

#
# clone tested apps
#

# WORKDIR /home/user/Projects
# RUN \
#   git clone "https://github.com/mbdevpl/ffb-mini" && \
#   git clone "https://github.com/mbdevpl/miranda_io"
