# eeg-qc-dash

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6326487.svg)](https://doi.org/10.5281/zenodo.6326487) [![Python](https://img.shields.io/badge/Python-3.6-green.svg)]() [![Platform](https://img.shields.io/badge/Platform-linux--64-orange.svg)]()


Billah, Tashrif; Bouix, Sylvain; Nicholas, Spero; Mathalon, Daniel; Light, Gregory;
Plotly/Dash based web application for checking quality of EEGs,
https://github.com/AMP-SCZ/eeg-qc-dash/, 2022, DOI: 10.5281/zenodo.6326487


### Flask vs uWSGI server

We have had many app crashes. We attributed the crashes to the development server Plotly uses as default: Flask.
Hence, we took up the task of installing uWSGI server. [These](https://github.com/AMP-SCZ/eeg-qc-dash/commit/09ab23ead95932b83f780043bb13e3aa599fcc25) changes were necessary for a Dash app to run via a uWSGI server.
The app visibly runs faster through uWSGI server as expected.


uWSGI was installed according to [official documentation](https://uwsgi-docs.readthedocs.io/en/latest/WSGIquickstart.html):

```bash
wget https://projects.unbit.it/downloads/uwsgi-latest.tar.gz
tar -zxvf uwsgi-latest.tar.gz
cd uwsgi-*
export PATH=~/miniconda3/bin/:$PATH
make
```

Notice that we used the main Python for uWSGI install, not an environment Python.
The latter does not have one dynamic library that is required to link with uWSGI.
Accordingly, you should run `pip install -r eeg-qc-dash/requirements.txt` on the main Python.


<details><summary>Build Python</summary>

In a new VM, even the main Python 3.9 did not come with `lib/libpython3.9.a`. So we had to build Python 3.9 from source
following https://docs.python.org/3/using/unix.html#building-python :

```bash
# as root
yum install libffi-devel libxml2-devel

# as non-root
wget https://www.python.org/ftp/python/3.9.11/Python-3.9.11.tgz
tar -zxvf Python-3.9.11.tgz
cd Python-3.9.11
./configure --prefix=`pwd`
make
make install

# create soft links
cd bin
ln -s python3.9 python
ln -s pip3 pip
cd ..

# make python3 available in PATH
export PATH=`pwd`/bin/:$PATH
export PYTHONHOME=`pwd`
```

Then uWSGI was built as above. `pip install -r eeg-qc-dash/requirements.txt` was also installed in this Python.

</details>


### Environment

Regardless of Flask or uWSGI server, the following environment variables are defined on the terminal:

```bash
export DASH_DEBUG=False
export DASH_URL_BASE_PATHNAME=/eegqc/
export EEG_QC_PHOENIX=/data/predict/data_from_nda/
export PATH=~/uwsgi-2.0.20/:~/miniconda3/bin/:$PATH
export PYTHONHOME=~/mininconda3/
cd ~/eeg-qc-dash/
```

Afterward, while it is just `./app.py` for Flask, uWSGI has a bit of intricate method for launching the app.
It can be done in two ways.


### 1. Launch uwsgi-nginx in http protocol

In this method, Nginx speaks http protocol to uWSGI. It can be slow.

The following section was added to `/etc/nginx.conf`:

```cfg
    location /eegqc/ {
      proxy_pass http://localhost:8050/;
    }
```

And uWSGI server was launched as follows:

> $ uwsgi --http :8050 --wsgi-file wsgi.py --master --processes 1 --threads 1





### 2. Launch uwsgi-nginx in wsgi protocol

In this method, Nginx speaks wsgi protocol to uWSGI. It is fast.

References: [digitalocean](https://www.digitalocean.com/community/tutorials/how-to-set-up-uwsgi-and-nginx-to-serve-python-apps-on-ubuntu-14-04)
and [uwsgi-docs](https://uwsgi-docs.readthedocs.io/en/latest/Nginx.html#configuring-nginx)

#### i. Using port (slower)

```cfg
    location /eegqc/ {
      include uwsgi_params;
      uwsgi_pass 127.0.0.1:8050;
    }
```

> $ uwsgi --socket :8050 --wsgi-file wsgi.py --master --processes 1 --threads 1

#### ii. Using socket (fastest)


```cfg
    location /eegqc/ {
      include uwsgi_params;
      uwsgi_pass unix:///run/uwsgi.sock;
    }
```


> $ uwsgi --socket /run/uwsgi.sock --wsgi-file uwsgi.py --master --processes 1 --chmod-socket=666


`/tmp/uwsgi.sock` could not be discovered by Nginx apparently because of [this](https://serverfault.com/a/464025) issue.
So we used `/run/uwsgi.sock`. Now it could be discovered but SELinux prevented Nginx from writing into it:

```bash
$ tail -f /var/log/messages
Oct 25 15:15:39 rc-predict setroubleshoot: SELinux is preventing nginx from connectto access on the unix_stream_socket /run/uwsgi.sock. For complete SELinux messages run: sealert -l 262f5c36-68ca-4eeb-a9ff-661a2f94a64e
```

To circumvent this permission deficit, we had to add a policy to SELinux according to [*Extend the httpd_t Domain Permissions*](https://www.nginx.com/blog/using-nginx-plus-with-selinux/).

The `httpd_can_network_connect` bool was set to 1 as usual.
