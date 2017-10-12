layout: post
comments: true
title: 'Using Ansible for OS initial setup to make it more flexible and less time-consuming'
tags:
  - 'Ansible'
  - 'Linux'
  - 'Debian'
  - 'i3wn'

# Introduction

Some Linux distros actually support unattended installation mode, which will
install a preconfigured image of an OS. Unfortunately, this is rather
time-consuming and the typical use case is provisioning of 100-s (or more)
identical servers with identical software.

In this post I'll try to achieve something similar (in sense, I'll try to
automate many processed) in desktop Linux installation. This post might
interest you, if you several pieces of hardware sharing a lot in their
software configuration.

# Software

Out goal will be to setup a desktop and a server-like machine, while minimizing
common configuration tasks.

In this post we will use

 * A windows host machine (yuck! this is not necessary)
 * Oracle VM Virtual Box
 * Debian 9 netinst distro image
 * Ansible (actually this is an Ansible tutorial for a special use-case)

# Our plans

  * We will use two separate git repositories: one for rapidly changing user
  settings (such `vim` config) and another one for the setup scripts (showing
  how to write them is the main goal of this post).

  * I recommend using some sort of Virtual Machine with snapshot capability
  &mdash; it help enormously with the trial-and-error process (which is
  inevitable). In out case Oracle VM Virtual Box.

# A boring part

Setting up an OS will be performed in manual mode. Basically, we will install
Debian 9 on virtual machine.

<img src="/assets/using-ansible/create-vm/1.png"/>
<img src="/assets/using-ansible/create-vm/2.png"/>
<img src="/assets/using-ansible/install-os/1.png"/>
<img src="/assets/using-ansible/install-os/2.png"/>
<img src="/assets/using-ansible/install-os/3.png"/>
<img src="/assets/using-ansible/install-os/4.png"/>

<img src="/assets/using-ansible/run/running.png"/>

## Some work for `root`

Login as root, install the `sudo` package and add user `miyuki` to the `sudo`
group. That's it.

    # login as root
    # apt install sudo
    # usermod -a -G sudo miyuki

logout and login as `miyuki`. Check that `sudo` works by running e.g.

    $ sudo ls

<img src="/assets/using-ansible/run/sudo.png"/>

# Getting the keys

In order to make out scripts work on VM, we need to get them there somehow.
Virtual Box Extensions (shared folders) cannot be install, because they
require X11 (for some reason). We have several options:

 - Install an SSH server on the machine an continue all out work via SSH. This
   options is OK for server configuration, but sucks for desktop (installing an
   SSH server just to uninstall it later is lame).
 - Use `rsync` or `scp` to copy the files from another box - seems OK, but will
   probably require some configuration of the VM network (this is true for the
   first option, too, BTW)
 - Use a media to copy out keys.

I preferred the third option and creates the following SSH config:

    Host bitbucket.org
    ControlMaster no
    PubkeyAuthentication yes
    IdentitiesOnly yes
    IdentityFile ~/.ssh/bitbucket_id

    Host ***
    PubkeyAuthentication yes
    IdentityFile ~/.ssh/provision_id
    IdentitiesOnly yes

I removed the host of my private Gitlab installation to defend from evil
hackers.

Besides this file we will of course need `bitbucket_id` and `provision_id`.
Create and ISO image containing these three files using your favorite tool and
mount the image into VM's virtual CD.

    $ mount /media/cdrom
    $ mkdir ~/.ssh && cd $/.ssh
    $ cp /media/cdrom/* .
    $ chmod 400 *
    $ cd ..

Don't forget the `chmod`. `SSH` does not like world-readable private keys (even
on single-user VMs).

We will need to install only a couple of packages for all the magic to happen:

    $ sudo apt-get install git ansible

## Running Ansible

Now:

    $ git clone ssh://git@***/miyuki/provisioning.git
    $ cd provisioning
    $ ansible-playbook desktop

Wait for about 15 minutes, reboot, and you can log on into you favorite window
manager (which is i3wm, I hope), start `vim` with all your favorite plugins
installed, maybe even run Google Chrome (which is not a part of Debian), if you
prefer it. Enjoy the console correctly with set up fonts. Needless to say that
Debian packages that you need are installed.

The rest of the post will discuss how to make this possible and also how to
install `vim` and its plugins on your home server, but not the x11 system using
the same code.

