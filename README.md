# ExtraBackup
ExtraBackup——为你的存档找一个（好几个）温馨的家

基于MCDR实现的存档分布式备份插件，可以自动将您的存档上传备份至另一块硬盘、nas甚至是百度网盘以防止服务器硬盘突然暴毙:P

目前只实现了本地硬盘的相应功能，ftp等功能仍在开发中

指令教程：

!!exb upload <id> <tag>           上传备份文件夹（一般就是pb_files下的export文件夹)中的指定文件， <id>为primebackup中的备份id，tag为自定义标签（可不写）

!!exb uploadall                   上传备份文件夹中的所有备份文件，自动跳过重复文件

!!exb download <file_name> <from> 下载指定备份路径中的备份文件到本地（from为备份路径名称，可留空，若留空则随机从一个可用的备份路径下载，file_name为文件名）

!!exb list <location>              列出备份路径下的所有文件，from留空为列出本地存档文件名

!!exb prnue <id>                  清理过时文件（id若不留空则清理指定备份（无视是否过时），可留空，如留空则清理所有过时文件，过时文件时间可以在config中设置）

!!exb delete <location> <id>      删除指定备份路径下的指定备份

!!exb lang <language>             切换语言，支持的语言：zh_cn,中文 ； en_us,英文

配置教程：

主配置：

{

  "enable":"false",     #是否启用该插件
  
  "language":"zh_cn",     #默认语言
  
  "max_thread":"-1",      #上传/下载最大线程数，-1为无限制
  
  "schedule_backup":{
  
      "enable":"false",        #是否启用定时上传备份
      
      "interval":"30m"          #上传时间间隔
      
  },
  
  "schedule_prune":{
  
      "enable":"false",          #是否启用定时清理
      
      "interval":"1d",            #定时清理时间间隔
      
      "max_lifetime":"3d"        #文件最大生命时间
      
  }
  
}

备份路径配置：

{

    "Name1":   #备份路径名称，支持中文
    
    {
    
        "enable":"false",                        #是否启用这个备份路径路径
        
        "mode":"ftp",                            #备份模式，"local":本地路径，为本地备份文件夹路径 “ftp”：ftp服务器模式
        
        "address":"ftp://example.com/folder",    #如果为local就写本地路径，ftp就写远程服务器地址
        
        "username":"username",                   #远程服务器登陆用户名，如果是本地地址就留空（双引号要留着不要删掉）
        
        "password":"123456"                      #远程服务器登陆密码，如果是本地地址就留空（双引号要留着不要删掉）
        
    },
    
    "Name2":
    
    {
    
        "enable":"true",
        
        "mode":"local",
        
        "address":"/folder/example",
        
        "username":"",
        
        "password":""
        
    }
    
}


