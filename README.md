## 開発環境
- vscode + pyenv + pipenv を想定
- python version は 3.11.2

## how to set up
clone したディレクトリで
```shell
pyenv local 3.11.2 \
&& pipenv --python 3.11.2 \
&& pipenv shell \
&& pipenv install
```
を実行し、vscodeでselect python interpreter→pipenvで作った環境を選択
