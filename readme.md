# QQ图片机器人

基于
[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)
和
[Stable Diffusion](https://github.com/AUTOMATIC1111/stable-diffusion-webui)
制作的QQ机器人，用于使用简单方式生成图片。

***

## 介绍

QQ的信息时间和消息发送使用go-http服务，图片生成使用python服务，两者通过http请求通讯。

图片生成服务由Stable Diffusion webui的API提供，同样通过http请求通讯。

图片审查模型使用[nsfw_model](https://github.com/GantMan/nsfw_model)

## 已实现的功能

根据抓取加入白名单的群和私聊中的关键字，解析prompt生成图片并以合并转发的形式发送。

图片缓存在本地，可以通过图片生成的ID进行重绘。

多种参数可以选择（分辨率，图片数量等）