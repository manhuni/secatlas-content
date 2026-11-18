# The content library of SecAtlas

This repository holds the library the SecAtlas app reads: the articles, their
editions in the seven languages of the library, the catalogue, the pictures and
the shared dictionary.

The content service of the app does not keep a copy. It reads this repository:

    https://secatlas-content.nguyenvanmanh-dev.workers.dev/v1/content/<article>

## How to change an article

1. Open the file of the article: `content/<article>.vi.json` for the
   Vietnamese edition, `content/<article>.ja.json` for the Japanese one, and
   so on. `content/<article>.json` is the English source.
2. Change the text. Keep the shape: the same sections, the same number of
   examples, the same terms.
3. Commit. The service serves the new text within a few minutes.

The release id of the library is the commit the files live in. The service
writes it into every answer, so the app knows that the library changed and
reads it again.

## What is generated and what is not

- `content/`, `catalog/`, `items/`, `assets/`, `aliases/`, `dictionary/`,
  `blob-metadata/` and `chunks/` are written by the tools of the house
  repository. A person may change the text of `content/`; the rest is built.
- `current.json` names the release the service reads. It is written after
  every push.
- The pictures are built from the media of the house repository, so a new
  picture is a new build, not a commit here.

The house repository is private: `manhuni/flt-gixsoft-secatlas-contents`.
