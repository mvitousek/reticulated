futen
=====

Ansible inventory file generating script from OpenSSH configuration file

# これは何？

OpenSSH の設定ファイルから Ansible のインベントリファイルを生成するスクリプトです。
主に Vagrant と Ansible を連携させることを想定しています。

Ansible は SSH 経由でホストをプロビジョニングします。
その為には接続の為の設定情報が必要ですが Ansible は OpenSSH の設定ファイルを読み込むことができます。
ですが、Ansible は接続する際のホストのポート番号については OpenSSH の設定ファイルではなく、インベントリファイルに記述する必要があるようです。
そして Vagrant はポートフォワーディング経由で仮想マシンへの SSH を提供しますが、使用するポートが常に同じという確証はありません。
つまり、Vagrant と Ansible を連携させる際には Vagrant から得られる仮想マシンの OpenSSH 設定からポート番号を見つけてインベントリファイルに記述しなければなりません。
これは、複数の仮想マシンを管理している場合には特に手間のかかる作業です。
futen はその作業を自動化します。

# インストール

インストールと実行には Python が必要です。

## GitHub のソースコードからインストールする

```
$ git clone https://github.com/momijiame/futen.git
$ cd futen
$ python setup.py install
```

## PIP でインストールする

```
$ pip install futen
```

# 使い方

## Vagrant と Ansible を連携させる

Vagrant で以下の 3 台の仮想マシンを管理している場合について考えます。

```
$ vagrant status
Current machine states:

web                       running (virtualbox)
app                       running (virtualbox)
db                        running (virtualbox)
```

vagrant ssh-config コマンドで OpenSSH の設定が得られます。

```
$ vagrant ssh-config web
Host web
  HostName 127.0.0.1
  User vagrant
  Port 2222
  UserKnownHostsFile /dev/null
  StrictHostKeyChecking no
  PasswordAuthentication no
  IdentityFile /Users/amedama/.vagrant.d/insecure_private_key
  IdentitiesOnly yes
  LogLevel FATAL
```

各仮想マシンの設定をファイルに書き出しましょう。

```
$ vagrant ssh-config web > ssh.config
$ vagrant ssh-config app >> ssh.config
$ vagrant ssh-config db >> ssh.config
```

ファイルの内容を futen の標準入力に渡すことで、ホスト名とポート番号から成るインベントリファイルが得られます。

```
$ cat ssh.config | futen > ansible_hosts
$ cat ansible_hosts 
web:2222
app:2200
db:2201
```

Ansible の設定ファイルを用意して、上記の設定ファイルを使うように指定しましょう。

```
$ cat << EOS > ansible.cfg
[defaults]
hostfile = ansible_hosts

[ssh_connection]
ssh_args = -F ssh.config

EOS
```

あとは Ansible のコマンドを実行するだけです。

```
$ ansible -m ping all
db | success >> {
    "changed": false, 
    "ping": "pong"
}

app | success >> {
    "changed": false, 
    "ping": "pong"
}

web | success >> {
    "changed": false, 
    "ping": "pong"
}
```

## より複雑なインベントリファイルを扱う

ロールなどを含むより複雑なインベントリファイルを扱う場合にはテンプレート機能が使えます。
まず、ホスト名を変数にしたインベントリファイルのテンプレートを用意します。
テンプレートの形式は Jinja2 です。

```
$ cat << EOS > inventory_template
[role1]
{{ web }}

[role2]
{{ app }}

[role3]
{{ db }}

[foo:bar]
{{ web }}

[hoge:fuga]
{{ app }}
{{ db }}

EOS
```

futen に -t オプションを指定することで、上記のテンプレートに内容をマージできます。

```
$ cat ssh.config | futen -t inventory_template > ansible_hosts
```

上記のテンプレートから以下のようなインベントリファイルが生成されます。

```
$ cat ansible_hosts 
[role1]
web:2222

[role2]
app:2200

[role3]
db:2201

[foo:bar]
web:2222

[hoge:fuga]
app:2200
db:2201
```
