# kana2 development notes

## Install dependencies

(Pybooru with the right commits isn't released yet on pip.)

    sudo pip3 install \
        https://github.com/ccc032/pybooru/archive/http-codes.zip \
        requests arrow whratio orderedset ujson --upgrade

## kanarip incompatibilities

- New default directory structure (can be changed): _<id>/<resource>.<ext>_
- If a media's extension can't be determined, it will be saved with _.None_
- No more errored files dir
- Full info JSONs are saved instead of just a list of tag
- Full artcom and notes JSONs are downloaded
- Meta files's equivalents are _<id>/extra.json_,
  their content differ from kanarip

* kanarip couldn't fetch notes for posts created in the last 24h
