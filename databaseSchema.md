## Albums

The structure in MongoDb of an album looks like this:

* `album`: Name of the album, for display.
* `albumPath`: sub-path to this album on disk (underneath `artistPath`)
* `artist`: Artist name for the *album* (which may be e.g. "Various Artists")
* `artistPath`: sub-path to this artist, relative to the music root dir
* `discNumber`: number of this disc in a multi-disc set (blank otherwise)
* `year`: The year of this release
* `tracks`: a list of track documents, where each contains:
   * `added`: datetime object when this track was moved into the library
   * `bitrate`: bitrate of this file, possibly average if this is VBR
   * `duration`: for display, duration of the file in 'MM:SS' format
   * `fileName`: full name of this file relative to the `albumPath` above
   * `genre`: string for display
   * `title`: track title for display
   * `trackArtist`: on a compilation, name of the performer to list for this track (else blank)
   * `trackArtistPath`: track artist in our internal Name-With-Dashes format
   * `trackNum`: track number as a string, with leading zeros if needed.



At some point we'll add entries for cover art in here as well.