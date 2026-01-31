import http.server
import json
import hashlib
import hmac
import os
import sys

# 用于验证GitHub webhook的密钥，在实际使用中应该从环境变量获取
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'your-secret-key')

class WebhookHandler(http.server.BaseHTTPRequestHandler):
    """处理GitHub webhook事件的HTTP处理器"""
    
    def do_POST(self):
        """处理POST请求"""
        if self.path != '/webhook':
            self.send_error(404, 'Not Found')
            return
        
        # 获取请求头
        content_length = int(self.headers.get('Content-Length', 0))
        signature = self.headers.get('X-Hub-Signature-256')
        event_type = self.headers.get('X-GitHub-Event')
        
        # 读取请求体
        body = self.rfile.read(content_length)
        
        # 验证签名
        if not self.verify_signature(body, signature):
            self.send_error(403, 'Invalid signature')
            return
        
        # 解析JSON数据
        try:
            data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_error(400, 'Invalid JSON')
            return
        
        # 处理不同类型的事件
        self.handle_event(event_type, data)
        
        # 发送响应
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'message': 'Webhook received successfully'}).encode('utf-8'))
    
    def verify_signature(self, payload, signature):
        """验证GitHub webhook签名"""
        if not signature:
            return False
        
        # 提取签名值
        signature_value = signature.split('=')[1]
        
        # 计算哈希值
        digest = hmac.new(
            WEBHOOK_SECRET.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # 比较签名
        return hmac.compare_digest(digest, signature_value)
    
    def handle_event(self, event_type, data):
        """处理不同类型的GitHub事件"""
        if event_type == 'push':
            print("\n=== 收到 Push 事件 ===")
            print(f"仓库: {data.get('repository', {}).get('full_name')}")
            print(f"分支: {data.get('ref', '').split('/')[-1]}")
            print(f"提交数量: {len(data.get('commits', []))}")
            print(f"推送者: {data.get('pusher', {}).get('name')}")
            
        elif event_type == 'pull_request':
            print("\n=== 收到 Pull Request 事件 ===")
            pr_data = data.get('pull_request', {})
            
            # 提取PR详细信息
            print(f"PR标题: {pr_data.get('title')}")
            print(f"PR编号: #{pr_data.get('number')}")
            print(f"作者: {pr_data.get('user', {}).get('login')}")
            print(f"状态: {pr_data.get('state')}")
            print(f"源分支: {pr_data.get('head', {}).get('ref')}")
            print(f"目标分支: {pr_data.get('base', {}).get('ref')}")
            print(f"PR URL: {pr_data.get('html_url')}")
            
            # 提取最新的提交信息
            latest_commit = pr_data.get('head', {}).get('commit', {})
            print(f"\n最新提交:")
            print(f"SHA: {latest_commit.get('sha')}")
            print(f"提交消息: {latest_commit.get('message')}")
            print(f"提交作者: {latest_commit.get('author', {}).get('name')}")
            print(f"提交日期: {latest_commit.get('author', {}).get('date')}")

def run_server(port=5000):
    """运行webhook服务器"""
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, WebhookHandler)
    print(f"Webhook服务器启动在端口 {port}...")
    print(f"Webhook端点: http://localhost:{port}/webhook")
    print(f"使用的密钥: {WEBHOOK_SECRET}")
    print("\n等待GitHub webhook事件...")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器正在关闭...")
        httpd.shutdown()
        print("服务器已关闭")

if __name__ == '__main__':
    # 从命令行参数获取端口号
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    
    run_server(port)
