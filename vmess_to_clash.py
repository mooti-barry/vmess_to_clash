import base64
import json
import yaml
import sys
import os
import re
from urllib.parse import urlparse, parse_qs

def decode_vmess(vmess_link):
    """
    解析 vmess 链接并返回配置信息
    
    Args:
        vmess_link: vmess://开头的链接
        
    Returns:
        dict: 包含 vmess 配置的字典
    """
    if not vmess_link.startswith('vmess://'):
        raise ValueError("链接必须以 vmess:// 开头")
    
    # 移除 vmess:// 前缀并解码 base64
    encoded_content = vmess_link[8:]
    try:
        decoded_content = base64.b64decode(encoded_content).decode('utf-8')
        config = json.loads(decoded_content)
        return config
    except Exception as e:
        raise ValueError(f"无法解析 vmess 链接: {e}")

def generate_clash_config(vmess_config):
    """
    根据 vmess 配置生成 clash 配置
    
    Args:
        vmess_config: 从 vmess 链接解析出的配置
        
    Returns:
        dict: Clash 配置字典
    """
    # 创建基本的 Clash 配置
    clash_config = {
        "port": 7890,
        "socks-port": 7891,
        "allow-lan": True,
        "mode": "rule",
        "log-level": "info",
        "external-controller": "127.0.0.1:9090",
        "proxies": [],
        "proxy-groups": [
            {
                "name": "PROXY",
                "type": "select",
                "proxies": ["自动选择"]
            },
            {
                "name": "自动选择",
                "type": "url-test",
                "url": "http://www.gstatic.com/generate_204",
                "interval": 300,
                "proxies": []
            }
        ],
        "rules": [
            "MATCH,PROXY"
        ]
    }
    
    # 创建代理配置
    proxy_name = vmess_config.get("ps", "Vmess节点")
    
    # 处理加密类型
    security = vmess_config.get("scy", "auto") or vmess_config.get("security", "auto")
    if security.lower() == "zero":
        security = "auto"  # 将"zero"映射为"auto"
    
    proxy = {
        "name": proxy_name,
        "type": "vmess",
        "server": vmess_config.get("add", ""),
        "port": int(vmess_config.get("port", 443)),
        "uuid": vmess_config.get("id", ""),
        "alterId": int(vmess_config.get("aid", 0)),
        "cipher": security,  # 使用处理后的加密类型
        "udp": True,
        "tls": vmess_config.get("tls", "") == "tls",
        "skip-cert-verify": True,
        "network": vmess_config.get("net", "tcp")
    }
    
    # 处理特殊网络类型的设置
    if proxy["network"] == "ws":
        proxy["ws-opts"] = {
            "path": vmess_config.get("path", "/"),
            "headers": {
                "host": vmess_config.get("host", "")
            }
        }
    
    # 添加代理到配置中
    clash_config["proxies"].append(proxy)
    
    # 添加代理到代理组
    clash_config["proxy-groups"][0]["proxies"].append(proxy_name)
    clash_config["proxy-groups"][1]["proxies"].append(proxy_name)
    
    return clash_config

def vmess_to_clash(vmess_link, output_file="config.yaml"):
    """
    将 vmess 链接转换为 clash 配置并保存到文件
    
    Args:
        vmess_link: vmess 链接
        output_file: 输出文件路径
    """
    try:
        # 解析 vmess 链接
        vmess_config = decode_vmess(vmess_link)
        
        # 生成 clash 配置
        clash_config = generate_clash_config(vmess_config)
        
        # 保存到文件
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(clash_config, f, allow_unicode=True, sort_keys=False)
        
        print(f"Clash 配置已保存到 {output_file}")
        return True
    except Exception as e:
        print(f"转换失败: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) > 1:
        vmess_link = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "config.yaml"
    else:
        vmess_link = input("请输入 vmess 链接 (以 vmess:// 开头): ")
        output_file = input("请输入输出文件名 (默认为 config.yaml): ") or "config.yaml"
    
    vmess_to_clash(vmess_link, output_file)

if __name__ == "__main__":
    main() 