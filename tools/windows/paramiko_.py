import paramiko
import time
import ini_
import os

class SSH:
  def __init__(self, ip, username, password, port, timeout=30):
    self.ip = ip
    self.username = username
    self.password = password
    self.port = int(port)
    self.timeout = timeout

    self.t = ''
    self.chan = ''
    # 链接失败的重试次数
    self.try_times = 3

  def connect(self, end_with="$ "):

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
      ssh.connect(hostname=self.ip, port=self.port,
                  username=self.username, password=self.password)
      self.channel = ssh.invoke_shell()
      time.sleep(0.1)
    except paramiko.ssh_exception.AuthenticationException:
      print('login failed...')
      exit(-1)

    buff = ''
    while not buff.endswith(end_with):
      resp = self.channel.recv(100)
      buff += resp.decode('utf-8')
    print("login successful...")

    return buff

  def __get_all_files_in_local_dir(self, local_dir):
    all_files = list()

    files = os.listdir(local_dir)
    for x in files:
      # local_dir目录中每一个文件或目录的完整路径
      filename = os.path.join(local_dir, x)
      # 如果是目录，则递归处理该目录
      if os.path.isdir(x):
        all_files.extend(self.__get_all_files_in_local_dir(filename))
      else:
        all_files.append(filename)
    return all_files

  def sftp_put_dir(self, local_dir, remote_dir):
    if not os.path.exists(remote_dir):
      os.makedirs(remote_dir)

    t = paramiko.Transport(sock=(self.ip, self.port))
    t.connect(username=self.username, password=self.password)
    sftp = paramiko.SFTPClient.from_transport(t)

    if remote_dir[-1] == '/':
      remote_dir = remote_dir[0:-1]

    # 获取本地指定目录及其子目录下的所有文件
    all_files = self.__get_all_files_in_local_dir(local_dir)
    # 依次put每一个文件
    for x in all_files:
      filename = os.path.split(x)[-1]
      remote_filename = remote_dir + '/' + filename
      sftp.put(x, remote_filename)
      print(u'%s file upload is complete!' % filename)

  def execute(self, command, end_with="$ "):
    sendcommand = command + "\n"
    self.channel.send(sendcommand)
    buff = ''
    while not buff.endswith(end_with):
      resp = self.channel.recv(100)
      buff += resp.decode('utf-8')
    print("execution result: \n %s " % buff)
    return buff


def get_ssh():
  my_ssh = SSH(ini_.host, ini_.username, ini_.password, ini_.port)
  my_ssh.connect()
  return my_ssh


def upload_linux():
  my_ssh = get_ssh()
  my_ssh.execute('mkdir ' + ini_.upload_dst_path)
  my_ssh.execute('sudo chmod -R 777 ' + ini_.upload_dst_path)
  my_ssh.execute('mkdir ' + ini_.put_dst_pwd)
  my_ssh.execute('sudo chmod -R 777 ' + ini_.put_dst_pwd)
  my_ssh.sftp_put_dir(ini_.upload_src_path, ini_.upload_dst_path)


def upload_zip():
  my_ssh = get_ssh()
  my_ssh.sftp_put_dir(ini_.put_src_pwd, ini_.put_dst_pwd)
  my_ssh.execute(ini_.python + ' ' + ini_.python_code)
