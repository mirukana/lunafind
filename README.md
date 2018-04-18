# kana2 development notes

## Install dependencies

(Pybooru with the right commits isn't released yet on pip.)

    sudo pip3 install https://git.io/vx2YG requests halo arrow whratio --upgrade

## kanarip incompatibilities

- Save JSONS in info/ instead of generating tags/ and meta/
- Errored files structure: {info,media,etc}/failed/id.ext instead of errors/...
- Download full artcom and notes

* kanarip couldn't fetch notes for posts created in the last 24h, this is fixed
