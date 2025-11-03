# ExtraBackup
ExtraBackup——为你的存档找一个（好几个）温馨的家

基于MCDR实现的存档分布式备份插件，可以自动将您的存档上传备份至另一块硬盘、nas甚至是百度网盘以防止服务器硬盘突然暴毙:(

目前只做了最基础的本地硬盘备份的功能，还有很多预期功能没做，随缘更新吧（

指令教程：

!!exb upload <file_name> 上传备份文件夹中的指定文件（file_name为文件名，需要包括后缀名，支持中文输入）

!!exb uploadall           上传备份文件夹中的所有备份文件，自动跳过重复文件

!!exb download <from> <file_name> 下载指定备份路径中的备份文件到本地（from为备份路径名称，file_name为文件名）

!!exb downloadall <from> 下载指定备份路径中的所有备份文件到本地（已经弃用，不建议使用）

!!exb list <from> 列出备份路径下的所有文件，from留空为列出本地存档文件名

!!exb prnue <where> 清理过时文件（where是备份路径名称，可留空，若留空则清理所有备份地址，若为local则清理本地备份位置）

配置教程：

主配置：

{

  "enable":"true",        #是否启用ExtraBackup插件
  
  "mode":"pb",            #启动模式，主要用于自动帮助定位存档文件夹;可选项："pb"：定位到pb的pb_files；  "local"：手动输入存档备份位置
  
  "localfolder":"",       #本地备份位置，如果选用pb模式，则留空
  
  "multithreading":"true",              #多线程模式是否开启
  
  "schedule_backup":{"enable":"false",  #是否开启定时上传备份
  
                     "interval":"30m"},  #定时时间间隔
                     
  "schedule_prnue":{"enable":"false",    #是否开启定时清理备份
  
                    "interval":"1d",     #清理间隔
                    
                    "max_lifetime":"1d"}   #文件最大创建时长，超过该时长的文件将被删除
                    
}

备份路径配置：

{

    "Name1":   #备份路径名称，支持中文
    
    {
    
        "enable":"false",                        #是否启用这个备份路径
        
        "mode":"ftp",                            #备份模式，"local":本地路径，为本地备份文件夹路径 “ftp”：ftp服务器模式
        
        "address":"ftp://example.com/folder",    #如果为local就写本地路径，ftp就写远程服务器地址
        
        "username":"username",                   #远程服务器登陆用户名，如果是本地地址就留空
        
        "password":"123456"                      #远程服务器登陆密码，如果是本地地址就留空
        
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


