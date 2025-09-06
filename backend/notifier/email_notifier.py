import smtplib 
from email.mime.text  import MIMEText
from email.mime.multipart  import MIMEMultipart 
from typing import Dict, List, Optional
from ..utils.logger  import logger
import json 
import ssl
 
class EmailNotifier:
    """
    邮件通知服务
    功能：
    - 发送交易信号、风控警报、系统异常通知 
    - 支持HTML/纯文本格式
    - 可配置多接收人
    """
 
    def __init__(self, config_path: str = "configs/notifier_config.json"): 
        """
        :param config_path: 邮件服务配置路径 
        配置示例：
        {
            "smtp_server": "smtp.gmail.com", 
            "smtp_port": 465,
            "sender_email": "yourbot@gmail.com", 
            "sender_password": "app_password",  # 使用应用专用密码 
            "receivers": ["trader1@example.com",  "trader2@example.com"] 
        }
        """
        self.config  = self._load_config(config_path)
        self.ssl_context  = ssl.create_default_context() 
 
    def _load_config(self, path: str) -> Dict:
        """加载邮件服务配置"""
        try:
            with open(path) as f:
                return json.load(f) 
        except Exception as e:
            logger.error(f" 加载邮件配置失败: {e}")
            raise
 
    def send_email(
        self,
        subject: str,
        content: str,
        content_type: str = "html",
        attachments: Optional[List[Dict]] = None
    ) -> bool:
        """
        发送邮件 
        :param subject: 邮件主题
        :param content: 邮件内容（支持HTML）
        :param content_type: html/plain
        :param attachments: [{"filename": "report.pdf",  "data": bytes}]
        :return: 是否发送成功
        """
        msg = MIMEMultipart()
        msg['From'] = self.config['sender_email'] 
        msg['To'] = ", ".join(self.config['receivers']) 
        msg['Subject'] = subject
 
        # 添加正文 
        msg.attach(MIMEText(content,  content_type))
 
        # 添加附件（可选）
        if attachments:
            for attach in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attach['data']) 
                encoders.encode_base64(part) 
                part.add_header( 
                    'Content-Disposition',
                    f'attachment; filename={attach["filename"]}'
                )
                msg.attach(part) 
 
        try:
            with smtplib.SMTP_SSL(
                self.config['smtp_server'], 
                self.config['smtp_port'], 
                context=self.ssl_context  
            ) as server:
                server.login( 
                    self.config['sender_email'], 
                    self.config['sender_password'] 
                )
                server.send_message(msg) 
            logger.info(f" 邮件发送成功: {subject}")
            return True 
        except Exception as e:
            logger.error(f" 邮件发送失败: {e}")
            return False 
 
    def notify_trade_signal(self, signal: Dict, exchange: str): 
        """发送交易信号通知"""
        subject = f"📈 交易信号 - {exchange.upper()}" 
        content = f"""
        <h3>新交易信号触发</h3>
        <table border="1">
            <tr><td>交易所</td><td>{exchange}</td></tr>
            <tr><td>交易对</td><td>{signal['symbol']}</td></tr>
            <tr><td>操作</td><td>{signal['action'].upper()}</td></tr>
            <tr><td>价格</td><td>{signal.get('price',  'N/A')}</td></tr>
            <tr><td>杠杆</td><td>{signal.get('leverage',  1)}x</td></tr>
        </table>
        """
        self.send_email(subject,  content)
 
    def notify_risk_alert(self, alert_type: str, symbol: str, details: str):
        """发送风控警报"""
        subject = f"⚠️ 风控警报 - {symbol} {alert_type}"
        content = f"""
        <h3>风控系统触发</h3>
        <p><b>类型:</b> {alert_type}</p>
        <p><b>交易对:</b> {symbol}</p>
        <p><b>详情:</b> {details}</p>
        """
        self.send_email(subject,  content)
 
    def notify_system_error(self, error: str, component: str = "Unknown"):
        """发送系统错误通知"""
        subject = f"❌ 系统异常 - {component}"
        content = f"""
        <h3>系统组件发生错误</h3>
        <p><b>组件:</b> {component}</p>
        <p><b>错误详情:</b></p>
        <pre>{error}</pre>
        """
        self.send_email(subject,  content)