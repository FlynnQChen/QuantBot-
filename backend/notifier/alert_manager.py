import time 
from typing import Dict, List, Optional, Union
from ..notifier.email_notifier  import EmailNotifier
from ..notifier.slack_notifier  import SlackNotifier  # 需实现 
from ..notifier.telegram_notifier  import TelegramNotifier  # 需实现
from ..utils.logger  import logger
from enum import Enum 
 
class AlertLevel(Enum):
    """警报级别定义"""
    INFO = 1 
    WARNING = 2
    CRITICAL = 3
 
class AlertManager:
    """
    智能警报管理器 
    功能：
    - 多通道通知（邮件/Slack/Telegram）
    - 基于级别的警报路由 
    - 防骚扰频率控制 
    """
 
    def __init__(self):
        self.notifiers  = {
            'email': EmailNotifier(),
            'slack': SlackNotifier(),  # 需实现 
            'telegram': TelegramNotifier()  # 需实现
        }
        self.alert_history  = {}  # 记录警报时间 {alert_key: [timestamps]}
        self.rate_limits  = {
            AlertLevel.INFO: 3600,    # 1小时1次
            AlertLevel.WARNING: 600,  # 10分钟1次 
            AlertLevel.CRITICAL: 60   # 1分钟1次 
        }
 
    def send_alert(
        self,
        message: str,
        level: AlertLevel = AlertLevel.INFO,
        channels: List[str] = None,
        data: Optional[Dict] = None,
        alert_key: Optional[str] = None 
    ) -> bool:
        """
        发送智能警报 
        :param message: 警报内容
        :param level: 警报级别（控制路由和频率）
        :param channels: 指定通道 ['email', 'slack']，为空则按级别自动选择 
        :param data: 附加数据（如交易信号详情）
        :param alert_key: 用于频率控制的唯一标识，为空则使用message 
        :return: 是否发送成功
        """
        # 频率检查 
        alert_key = alert_key or message
        if self._check_rate_limit(alert_key, level):
            logger.warning(f" 警报频率受限 [{alert_key}]")
            return False
 
        # 确定通知通道
        channels = channels or self._select_channels_by_level(level)
        
        # 格式化消息 
        formatted = self._format_message(message, level, data)
        
        # 多通道发送
        results = []
        for channel in channels:
            if channel not in self.notifiers: 
                logger.error(f" 未知通知通道: {channel}")
                continue 
            
            try:
                if channel == 'email':
                    results.append( 
                        self.notifiers[channel].send_email( 
                            subject=f"[{level.name}]  交易系统警报",
                            content=formatted['html'],
                            content_type='html'
                        )
                    )
                elif channel == 'slack':
                    results.append( 
                        self.notifiers[channel].send_message( 
                            text=formatted['text'],
                            blocks=formatted.get('slack_blocks') 
                        )
                    )
                elif channel == 'telegram':
                    results.append( 
                        self.notifiers[channel].send_message( 
                            text=formatted['text'],
                            parse_mode='HTML'
                        )
                    )
            except Exception as e:
                logger.error(f" 通道 {channel} 发送失败: {e}")
                results.append(False) 
 
        # 记录发送时间
        self._record_alert_time(alert_key)
        return any(results)
 
    def _select_channels_by_level(self, level: AlertLevel) -> List[str]:
        """根据警报级别选择通道"""
        if level == AlertLevel.CRITICAL:
            return ['email', 'slack', 'telegram']
        elif level == AlertLevel.WARNING:
            return ['email', 'slack']
        return ['email']
 
    def _format_message(self, message: str, level: AlertLevel, data: Dict) -> Dict:
        """格式化多通道消息内容"""
        # 基础文本 
        text = f"[{level.name}]  {message}" 
        
        # HTML版本（邮件用）
        html = f"""
        <h2 style="color: {self._get_color_by_level(level)}">{level.name}</h2> 
        <p>{message}</p>
        """
        if data:
            html += "<ul>"
            for k, v in data.items(): 
                html += f"<li><b>{k}:</b> {v}</li>"
            html += "</ul>"
 
        # Slack Blocks（可选）
        blocks = None
        if data and 'slack' in self.notifiers: 
            blocks = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{level.name}*:  {message}"}
                },
                {
                    "type": "divider"
                }
            ]
            for k, v in data.items(): 
                blocks.append({ 
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"• *{k}*: {v}"}
                })
 
        return {
            'text': text,
            'html': html,
            'slack_blocks': blocks 
        }
 
    def _get_color_by_level(self, level: AlertLevel) -> str:
        """获取级别对应颜色"""
        return {
            AlertLevel.INFO: "#3498db",
            AlertLevel.WARNING: "#f39c12",
            AlertLevel.CRITICAL: "#e74c3c"
        }[level]
 
    def _check_rate_limit(self, alert_key: str, level: AlertLevel) -> bool:
        """检查是否超过频率限制"""
        if level == AlertLevel.CRITICAL:
            return False  # 关键警报不受限
        
        history = self.alert_history.get(alert_key,  [])
        now = time.time() 
        valid_window = now - self.rate_limits[level] 
        
        # 清理过期记录
        recent_alerts = [t for t in history if t > valid_window]
        self.alert_history[alert_key]  = recent_alerts
        
        return len(recent_alerts) >= 1
 
    def _record_alert_time(self, alert_key: str):
        """记录警报发送时间"""
        if alert_key not in self.alert_history: 
            self.alert_history[alert_key]  = []
        self.alert_history[alert_key].append(time.time()) 
 
    # ----------- 快捷方法 -----------
    def notify_trade_signal(self, signal: Dict, exchange: str):
        """发送交易信号（自动格式化）"""
        self.send_alert( 
            message=f"交易信号 - {exchange.upper()}  {signal['symbol']}",
            level=AlertLevel.INFO,
            data={
                "Action": signal['action'].upper(),
                "Price": signal.get('price',  'N/A'),
                "Leverage": f"{signal.get('leverage',  1)}x"
            },
            alert_key=f"trade_{exchange}_{signal['symbol']}"
        )
 
    def notify_risk_event(self, event_type: str, symbol: str, details: str):
        """发送风控事件警报"""
        self.send_alert( 
            message=f"风控触发 - {symbol} {event_type}",
            level=AlertLevel.WARNING,
            data={
                "Symbol": symbol,
                "Event": event_type,
                "Details": details 
            },
            alert_key=f"risk_{symbol}_{event_type}"
        )