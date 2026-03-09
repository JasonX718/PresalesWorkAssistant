"""
Bootstrap module.

Handles initial data loading for the knowledge base.
Generates seed data and imports it to reach the 1000-record target.
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional

from app.knowledge.chunker import chunk_text
from app.knowledge.embeddings import get_embedding_service
from app.knowledge.vector_store import get_vector_store
from app.knowledge.dedup import DeduplicationService
from app.models.knowledge import BootstrapResponse
from config import get_settings

logger = logging.getLogger(__name__)


def load_seed_files(seed_dir: str) -> list[dict]:
    """
    Load seed data from JSON files in the seed directory.

    Each JSON file should contain a list of objects with:
    - title: str
    - content: str
    - document_type: str (optional)
    """
    records = []
    path = Path(seed_dir)

    if not path.exists():
        logger.warning(f"Seed directory not found: {seed_dir}")
        return records

    for json_file in sorted(path.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "content" in item:
                        records.append({
                            "title": item.get("title", json_file.stem),
                            "content": item["content"],
                            "document_type": item.get("document_type", "seed"),
                            "source": f"seed:{json_file.name}",
                        })
            elif isinstance(data, dict) and "content" in data:
                records.append({
                    "title": data.get("title", json_file.stem),
                    "content": data["content"],
                    "document_type": data.get("document_type", "seed"),
                    "source": f"seed:{json_file.name}",
                })

            logger.info(f"Loaded {len(records)} records from {json_file.name}")
        except Exception as e:
            logger.error(f"Error loading seed file {json_file}: {e}")

    return records


def generate_synthetic_seed_data() -> list[dict]:
    """
    Generate synthetic seed data for bootstrapping.

    Creates a comprehensive set of ZStack-related knowledge entries
    covering common topics, FAQs, troubleshooting, and architecture docs.
    """
    categories = {
        "architecture": _generate_architecture_docs(),
        "troubleshooting": _generate_troubleshooting_docs(),
        "faq": _generate_faq_docs(),
        "deployment": _generate_deployment_docs(),
        "api": _generate_api_docs(),
        "networking": _generate_networking_docs(),
        "storage": _generate_storage_docs(),
        "compute": _generate_compute_docs(),
        "security": _generate_security_docs(),
        "operations": _generate_operations_docs(),
    }

    records = []
    for doc_type, docs in categories.items():
        for doc in docs:
            doc["document_type"] = doc_type
            doc["source"] = f"seed:synthetic:{doc_type}"
            records.append(doc)

    return records


def _generate_architecture_docs() -> list[dict]:
    return [
        {"title": "ZStack Cloud整体架构概述",
         "content": """ZStack Cloud是一款基于Java开发的开源IaaS云平台软件。采用微服务架构设计，核心管理节点(Management Node)负责资源调度和管理。
系统核心组件包括：管理节点(MN)、计算节点(KVM Host)、存储系统、网络系统。
管理节点采用无状态设计，支持多节点高可用部署。所有消息通过RabbitMQ消息总线进行异步通信。
数据持久化使用MySQL数据库，支持主从复制。管理节点通过Agent与计算节点和存储节点通信。"""},
        {"title": "ZStack管理节点高可用架构",
         "content": """ZStack管理节点支持双节点高可用部署。使用HAProxy进行负载均衡，Keepalived实现VIP漂移。
部署要求：两台管理节点服务器，共享MySQL数据库（主从或Galera集群），共享RabbitMQ。
故障切换时间通常在30秒以内。管理节点无状态设计意味着任何节点故障不会导致正在运行的云主机受影响。
配置步骤：1.部署双管理节点 2.配置HAProxy 3.配置Keepalived 4.配置共享数据库 5.验证故障切换。"""},
        {"title": "ZStack消息总线架构",
         "content": """ZStack使用RabbitMQ作为消息总线，所有组件间通信基于异步消息。每个服务在启动时注册自己的Queue。
消息类型包括：APIMessage(API请求)、NeedReplyMessage(需要回复的消息)、Event(事件通知)。
消息处理采用链式模型，支持消息拦截和预处理。所有API操作都转换为内部消息进行处理。
消息超时机制确保系统不会因某个服务无响应而挂起。默认超时时间为30分钟，可配置。"""},
        {"title": "ZStack数据库设计原则",
         "content": """ZStack使用MySQL存储所有资源状态和配置信息。采用软删除机制，删除的资源标记deleted字段而非物理删除。
每个资源表都包含uuid、name、description、createDate、lastOpDate等标准字段。
资源间关系通过外键或关联表维护。使用乐观锁处理并发更新。
数据库版本升级通过Flyway进行schema迁移管理。支持MySQL 5.7+和MariaDB 10.x。"""},
        {"title": "ZStack API设计架构",
         "content": """ZStack提供RESTful HTTP API和SDK访问方式。所有API遵循统一的请求-响应模式。
API认证使用Session机制：先通过LogInByAccount获取session，后续请求携带sessionId。
API分为同步和异步两种：查询操作同步返回，创建/修改操作异步执行并返回任务UUID。
客户端通过轮询或WebSocket获取异步操作结果。提供Java/Python/Go等多语言SDK。"""},
        {"title": "ZStack插件架构设计",
         "content": """ZStack采用微内核+插件的架构设计。核心引擎提供基础的资源管理和消息路由能力。
功能通过插件形式扩展：如KVM虚拟化插件、Ceph存储插件、VPC网络插件等。
插件通过Extension Point机制挂载到核心流程中。支持在不修改核心代码的情况下扩展功能。
插件生命周期由框架统一管理，支持动态加载和卸载。"""},
        {"title": "ZStack Cloud资源模型",
         "content": """ZStack的资源模型采用层次化设计。顶层是Zone（区域），代表一个物理数据中心。
Zone下包含Cluster（集群）、PrimaryStorage（主存储）、L2Network（二层网络）。
Cluster下挂载Host（物理机），Host上运行VM（云主机）。
云主机关联Volume（云盘）、NIC（网卡）、SecurityGroup（安全组）等资源。
镜像存储在BackupStorage（镜像服务器）上，使用时下载到PrimaryStorage。"""},
        {"title": "ZStack工作流引擎",
         "content": """ZStack使用自研的FlowChain工作流引擎处理复杂的多步骤操作。
每个操作被分解为一系列Flow（步骤），每个Flow可以定义正向操作和回滚操作。
工作流支持自动回滚：当某一步失败时，已完成的步骤按逆序执行回滚。
工作流支持并行执行、条件分支和超时控制。所有长时间操作都基于工作流实现。"""},
        {"title": "ZStack调度器设计",
         "content": """ZStack的调度器负责将云主机分配到合适的物理机上运行。
调度过程分为两个阶段：过滤（Filter）和排序（Sort）。
过滤阶段排除不满足条件的物理机（如CPU/内存不足、存储不兼容等）。
排序阶段对候选物理机打分，选择最优目标。支持自定义调度策略。
内置策略包括：资源均衡、最小负载、指定物理机等。"""},
        {"title": "ZStack全局配置系统",
         "content": """ZStack使用GlobalConfig系统管理所有可配置参数。
GlobalConfig支持运行时修改，无需重启服务。通过API或UI即可调整。
配置项分类管理：如vm.cpuNum.max控制云主机最大CPU数，host.ping.interval控制心跳间隔。
配置变更会触发事件通知，相关组件自动应用新配置。支持配置导出和导入。"""},
    ]


def _generate_troubleshooting_docs() -> list[dict]:
    return [
        {"title": "云主机创建失败排查",
         "content": """问题：云主机创建失败
常见原因：
1. 物理机资源不足（CPU/内存/存储）
2. 镜像下载失败或损坏
3. 网络DHCP分配失败
4. 存储连接异常

排查步骤：
1. 查看管理节点日志：/usr/local/zstack/apache-tomcat/logs/management-server.log
2. 查看任务详情：zstack-cli QueryTask
3. 检查物理机可用资源：zstack-cli QueryHost
4. 检查存储容量：zstack-cli QueryPrimaryStorage
5. 检查网络服务：zstack-cli QueryL3Network

临时方案：尝试指定其他物理机创建，或清理存储空间。"""},
        {"title": "管理节点无法启动排查",
         "content": """问题：ZStack管理节点启动失败
常见原因：
1. MySQL数据库连接失败
2. RabbitMQ服务未启动
3. 端口被占用（8080/8443）
4. Java内存不足
5. 配置文件错误

排查步骤：
1. 检查MySQL状态：systemctl status mariadb
2. 检查RabbitMQ状态：systemctl status rabbitmq-server
3. 查看启动日志：cat /usr/local/zstack/apache-tomcat/logs/catalina.out
4. 检查端口：netstat -tlnp | grep 8080
5. 检查配置：cat /usr/local/zstack/apache-tomcat/webapps/zstack/WEB-INF/classes/zstack.properties

临时方案：使用zstack-ctl start --debug启动查看详细错误信息。"""},
        {"title": "云主机无法连接网络排查",
         "content": """问题：云主机创建成功但无法联网
常见原因：
1. 虚拟路由器未正常工作
2. DHCP服务异常
3. 安全组规则限制
4. 物理网络问题

排查步骤：
1. 检查虚拟路由器状态：zstack-cli QueryVirtualRouterVm
2. 登录虚拟路由器检查DHCP：virsh console xxx
3. 检查安全组规则
4. 检查物理机网桥：brctl show
5. 在物理机上抓包确认：tcpdump -i br_eth0

临时方案：重启虚拟路由器或重新连接云主机网络。"""},
        {"title": "存储空间不足处理",
         "content": """问题：主存储空间不足导致业务异常
症状：云主机无法创建、快照失败、云盘扩容失败

排查步骤：
1. 查看存储使用率：zstack-cli QueryPrimaryStorage
2. 检查实际存储空间：df -h（本地存储）或ceph df（Ceph）
3. 查找大文件：find /zstack_ps -size +10G
4. 检查快照占用空间
5. 检查回收站数据

清理方案：
1. 清理过期快照
2. 清空回收站：zstack-cli ExpungeImage / ExpungeVmInstance
3. 删除无用云盘和镜像
4. 扩容存储

监控建议：设置存储使用率告警阈值80%。"""},
        {"title": "物理机连接断开排查",
         "content": """问题：物理机状态显示Disconnected
常见原因：
1. 物理机宕机或重启
2. 管理网络中断
3. Agent服务异常
4. 心跳超时

排查步骤：
1. Ping物理机管理IP
2. SSH登录物理机检查
3. 检查Agent状态：systemctl status zstack-kvmagent
4. 查看Agent日志：/var/log/zstack/zstack-kvmagent.log
5. 检查管理节点到物理机的连接

恢复步骤：
1. 确认物理机在线
2. 重启Agent：systemctl restart zstack-kvmagent
3. 在UI或CLI重新连接物理机
4. 确认物理机上的云主机状态"""},
        {"title": "镜像上传失败排查",
         "content": """问题：镜像上传到镜像服务器失败
常见原因：
1. 镜像服务器空间不足
2. 网络传输超时
3. 镜像格式不支持
4. HTTP服务异常

排查步骤：
1. 检查镜像服务器空间：df -h
2. 检查网络连通性
3. 确认镜像格式（支持qcow2/raw/vmdk/iso）
4. 查看管理节点日志中的上传错误
5. 检查镜像服务器服务状态

临时方案：使用命令行直接上传到镜像服务器目录，然后通过API注册。"""},
        {"title": "云主机迁移失败排查",
         "content": """问题：云主机在线/离线迁移失败
常见原因：
1. 目标物理机资源不足
2. 共享存储未挂载
3. CPU型号不兼容
4. 网络配置不一致

排查步骤：
1. 检查目标物理机资源
2. 确认共享存储在源和目标都已挂载
3. 检查CPU兼容性：virsh capabilities
4. 查看迁移日志
5. 检查libvirt版本一致性

解决方案：
1. 使用CPU透传模式
2. 确保网桥和网络配置一致
3. 离线迁移替代在线迁移"""},
        {"title": "数据库性能问题排查",
         "content": """问题：管理节点响应变慢，数据库负载高
症状：API响应时间长、UI操作卡顿

排查步骤：
1. 检查MySQL状态：mysqladmin status
2. 查看慢查询：show variables like 'slow_query%';
3. 检查连接数：show status like 'Threads_connected';
4. 查看锁等待：show engine innodb status;
5. 检查磁盘IO：iostat -x 1

优化建议：
1. 开启慢查询日志分析
2. 适当增加连接池大小
3. 定期清理历史任务数据
4. 考虑使用SSD存储数据库文件"""},
        {"title": "VPC网络故障排查",
         "content": """问题：VPC网络内云主机间无法通信或无法访问外网
常见原因：
1. VPC路由器异常
2. 网络服务（SNAT/DNAT/EIP）配置错误
3. 安全组或ACL规则阻断
4. 底层VXLAN或VLAN配置问题

排查步骤：
1. 检查VPC路由器状态
2. 检查网络服务配置
3. 登录VPC路由器检查路由表和iptables
4. 检查物理交换机VLAN配置
5. 在物理机上进行网络抓包分析

修复步骤：
1. 重启VPC路由器的网络服务
2. 重新配置有问题的网络服务
3. 如VPC路由器异常，进行重连操作"""},
        {"title": "备份恢复失败排查",
         "content": """问题：云主机备份或从备份恢复失败
常见原因：
1. 镜像服务器空间不足
2. 快照链损坏
3. 存储IO瓶颈
4. 网络传输超时

排查步骤：
1. 检查备份存储空间
2. 查看备份任务日志
3. 检查快照完整性
4. 监控存储IO性能
5. 检查网络带宽使用情况

建议：
1. 实施定期备份策略
2. 监控备份存储容量
3. 在低峰期执行备份操作
4. 验证备份可恢复性"""},
    ]


def _generate_faq_docs() -> list[dict]:
    return [
        {"title": "ZStack支持哪些虚拟化技术",
         "content": """ZStack Cloud主要支持KVM虚拟化技术。KVM是Linux内核内置的虚拟化模块，性能接近物理机。
ZStack也支持通过vCenter管理VMware ESXi环境，实现异构虚拟化统一管理。
支持的Guest OS包括：CentOS/RHEL 6/7/8、Ubuntu 16/18/20/22、Windows Server 2012/2016/2019/2022、Windows 10/11等。
CPU虚拟化要求物理机支持VT-x(Intel)或AMD-V(AMD)技术。"""},
        {"title": "ZStack的许可证模式",
         "content": """ZStack提供社区版和企业版两种许可证模式。
社区版：开源免费，功能受限，适合学习和测试。
企业版：商业授权，按物理机CPU颗数授权。提供完整功能和商业技术支持。
企业版提供标准版和高级版，高级版包含混合云、容灾、GPU虚拟化等高级功能。
授权采用License文件方式，通过UI导入即可激活。"""},
        {"title": "ZStack最低硬件要求",
         "content": """管理节点最低要求：
- CPU: 4核
- 内存: 8GB (推荐16GB)
- 存储: 100GB SSD
- 网络: 千兆网卡

计算节点最低要求：
- CPU: 支持VT-x/AMD-V，推荐8核以上
- 内存: 16GB以上（根据云主机数量）
- 存储: 根据存储方案确定
- 网络: 千兆网卡（推荐万兆）

测试环境可以使用单节点部署（管理+计算合一）。"""},
        {"title": "ZStack支持哪些存储方案",
         "content": """ZStack支持多种存储方案：
1. 本地存储（LocalStorage）：使用物理机本地磁盘，简单但不支持迁移。
2. NFS/共享存储：通过NFS协议访问共享存储，支持在线迁移。
3. Ceph：分布式存储，高可靠高性能，推荐生产环境使用。
4. SAN存储：通过iSCSI/FC协议接入企业级SAN存储。
5. Shared Block：共享块存储方案，适合少量节点场景。

推荐方案：
- 小规模(<10台)：本地存储 + NFS
- 中等规模：Ceph
- 企业级：Ceph 或 SAN"""},
        {"title": "如何规划ZStack网络",
         "content": """ZStack网络规划建议：
1. 管理网络：管理节点与计算节点通信，建议独立VLAN。
2. 存储网络：存储流量专用，建议万兆。
3. 业务网络：云主机对外通信，可使用VLAN或VXLAN隔离。

网络模式选择：
- 扁平网络：简单，云主机直接获取物理网络IP。
- VPC网络：隔离性好，支持NAT/EIP/LB等网络服务。
- 经典网络+安全组：传统模式，通过安全组实现隔离。

建议至少规划两个物理网络：管理+存储网络 和 业务网络。"""},
        {"title": "ZStack如何实现高可用",
         "content": """ZStack多层次高可用方案：
1. 管理节点HA：双节点+HAProxy+Keepalived
2. 计算节点HA：物理机故障自动将云主机迁移到其他节点
3. 存储HA：Ceph三副本或SAN存储多路径
4. 网络HA：VPC路由器双节点部署
5. 数据库HA：MySQL主从复制或Galera集群

自动故障检测机制：
- 管理节点通过心跳检测物理机状态
- 物理机故障后自动触发HA恢复流程
- HA恢复优先级可配置

注意：HA需要使用共享存储（非本地存储）。"""},
        {"title": "ZStack备份策略建议",
         "content": """建议的备份策略：
1. 云主机快照：定期创建，保留最近3-5个
2. 云盘备份：重要数据定期备份到镜像服务器
3. 数据库备份：每天全量备份MySQL数据
4. 配置备份：定期导出全局配置

自动化备份：
- 使用ZStack定时任务功能自动创建快照
- 编写脚本自动备份数据库
- 使用crontab定期执行备份

灾备方案：
- 同城灾备：两个数据中心主从复制
- 异地灾备：ZStack灾备功能（企业高级版）"""},
        {"title": "ZStack Cloud升级流程",
         "content": """ZStack Cloud升级步骤：
1. 备份数据库：mysqldump -u root zstack > backup.sql
2. 备份管理节点配置
3. 下载升级包
4. 停止管理节点：zstack-ctl stop
5. 执行升级：bash ZStack-installer.bin -u
6. 启动管理节点：zstack-ctl start
7. 验证服务正常

注意事项：
- 建议先在测试环境验证
- 不支持跨大版本升级
- 升级过程中云主机不受影响
- 双管理节点需逐个升级"""},
        {"title": "ZStack性能调优建议",
         "content": """系统性能调优：
1. 管理节点：增加JVM堆内存（-Xmx8g）
2. 数据库：调整innodb_buffer_pool_size（物理内存的60-70%）
3. 存储：使用SSD、启用缓存
4. 网络：启用巨帧(MTU 9000)、使用SR-IOV

云主机性能优化：
1. 使用virtio驱动
2. 启用大页内存(HugePages)
3. CPU绑定(CPU Pinning)
4. NUMA亲和性配置

监控建议：
1. 部署Prometheus+Grafana监控
2. 关注CPU/内存/存储/网络使用率
3. 设置告警阈值"""},
        {"title": "ZStack与其他云平台的区别",
         "content": """ZStack vs OpenStack：
- ZStack：架构简洁、部署快速（30分钟）、性能好、学习成本低
- OpenStack：功能全面但架构复杂、部署运维难度大

ZStack vs VMware vSphere：
- ZStack：开源、成本低、支持国产化、API丰富
- VMware：生态成熟但授权费高、不支持国产化

ZStack优势：
1. 4秒创建云主机
2. 全API设计，自动化能力强
3. 支持国产CPU和操作系统
4. 无锁架构，高并发性能好
5. 30分钟完成部署"""},
    ]


def _generate_deployment_docs() -> list[dict]:
    return [
        {"title": "ZStack单节点快速部署",
         "content": """单节点部署（管理+计算合一）：
环境要求：CentOS 7.x / Kylin V10 / UOS，至少8GB内存

步骤：
1. 下载安装包：wget https://download.zstack.io/releases/ZStack-installer.bin
2. 执行安装：bash ZStack-installer.bin -a
3. 等待安装完成（约15-30分钟）
4. 访问UI：http://<IP>:5000
5. 默认账户：admin / password

安装后配置：
1. 添加Zone和Cluster
2. 添加当前节点为Host
3. 添加存储（本地存储即可）
4. 添加网络
5. 上传镜像，创建云主机"""},
        {"title": "ZStack生产环境部署架构",
         "content": """生产环境推荐架构：
管理节点：2台（HA部署）
计算节点：3台以上
存储：Ceph集群（3节点以上）或SAN存储

网络规划：
- 管理网络：10.0.0.0/24（VLAN 100）
- 存储网络：10.0.1.0/24（VLAN 101）万兆
- 业务网络：VLAN 200-300

部署顺序：
1. 部署数据库和消息队列
2. 部署第一个管理节点
3. 配置HA，部署第二个管理节点
4. 添加计算节点
5. 配置存储
6. 配置网络
7. 功能验证"""},
        {"title": "Ceph存储集群部署",
         "content": """Ceph集群部署指南：
节点要求：至少3个OSD节点、3个MON节点（可复用）

部署步骤：
1. 准备节点（关闭防火墙、配置NTP、配置SSH免密）
2. 安装ceph-deploy：pip install ceph-deploy
3. 初始化集群：ceph-deploy new node1 node2 node3
4. 安装Ceph：ceph-deploy install node1 node2 node3
5. 初始化MON：ceph-deploy mon create-initial
6. 添加OSD：ceph-deploy osd create node1:sdb node2:sdb node3:sdb
7. 创建存储池：ceph osd pool create zstack 128

在ZStack中接入：
1. 添加Ceph主存储：填入MON地址和池名称
2. 添加Ceph镜像服务器
3. 验证连接正常"""},
        {"title": "ZStack网络部署配置",
         "content": """网络配置详细步骤：

扁平网络配置：
1. 创建L2Network（二层网络），指定物理接口
2. 创建L3Network（三层网络），设置IP范围
3. 添加DNS服务
4. 创建云主机时选择该网络

VPC网络配置：
1. 创建VPC
2. 创建VPC下的子网络
3. 配置路由器
4. 配置SNAT（出网）
5. 配置EIP或端口转发（入网）
6. 创建云主机加入VPC网络

注意：VPC网络的物理网络需要支持VXLAN，物理交换机需放通UDP 4789端口。"""},
        {"title": "ZStack对接vCenter部署",
         "content": """ZStack管理VMware环境配置步骤：
1. 确保vCenter已部署并正常运行
2. 在ZStack中添加vCenter资源：
   - 提供vCenter地址、用户名、密码
   - ZStack自动同步ESXi主机、虚拟机、网络、存储信息
3. 同步完成后可通过ZStack统一管理

功能支持：
- 创建/启停/删除VMware虚拟机
- 虚拟机生命周期管理
- 网络和存储管理
- 监控和日志
- 不支持：在线迁移、快照（使用VMware原生快照）"""},
    ]


def _generate_api_docs() -> list[dict]:
    return [
        {"title": "ZStack API认证流程",
         "content": """API认证步骤：
1. 登录获取Session：
POST /v1/accounts/login
{
  "logInByAccount": {
    "accountName": "admin",
    "password": "your_password_sha512"
  }
}
注意：密码需要SHA-512加密

2. 获取sessionId后，后续请求在Header中携带：
Authorization: OAuth {sessionId}

3. Session有效期默认6小时，可通过GlobalConfig调整
4. 退出登录：DELETE /v1/accounts/sessions/{sessionId}"""},
        {"title": "ZStack CLI使用指南",
         "content": """ZStack CLI(zstack-cli)是命令行管理工具。

常用命令：
- 登录：zstack-cli LogInByAccount accountName=admin password=xxx
- 查询云主机：zstack-cli QueryVmInstance
- 创建云主机：zstack-cli CreateVmInstance name=test ...
- 查询物理机：zstack-cli QueryHost
- 查询存储：zstack-cli QueryPrimaryStorage

查询高级用法：
- 条件过滤：QueryVmInstance state=Running
- 排序：QueryVmInstance sortBy=createDate sortDirection=desc
- 分页：QueryVmInstance start=0 limit=10
- 字段选择：QueryVmInstance fields=uuid,name,state"""},
        {"title": "ZStack REST API示例",
         "content": """常用REST API示例：

创建云主机：
POST /v1/vm-instances
{
  "params": {
    "name": "test-vm",
    "instanceOfferingUuid": "xxx",
    "imageUuid": "xxx",
    "l3NetworkUuids": ["xxx"],
    "defaultL3NetworkUuid": "xxx"
  }
}

查询云主机：
GET /v1/vm-instances
GET /v1/vm-instances/{uuid}

启动云主机：
PUT /v1/vm-instances/{uuid}/actions
{"startVmInstance": {}}

停止云主机：
PUT /v1/vm-instances/{uuid}/actions
{"stopVmInstance": {}}

所有API返回格式：
{"inventory": {...}} 或 {"inventories": [...]}"""},
        {"title": "ZStack Webhook和事件通知",
         "content": """ZStack支持通过Webhook接收事件通知：

创建Webhook：
POST /v1/web-hooks
{
  "params": {
    "name": "vm-events",
    "url": "http://your-server/webhook",
    "type": "EventSubscription",
    "opaque": "VmInstanceInventory"
  }
}

支持的事件类型：
- 云主机生命周期事件（创建、删除、启停、迁移）
- 物理机状态变更
- 存储容量变更
- 告警事件

Webhook回调数据包含完整的资源信息和事件详情。"""},
        {"title": "ZStack SDK使用",
         "content": """ZStack提供多语言SDK：

Python SDK示例：
```python
import zstacklib.utils.http as http

# 登录
session = api.login_by_account("admin", "password")

# 查询云主机
vms = api.query_vm_instance(conditions=["state=Running"])

# 创建云主机
vm = api.create_vm_instance(
    name="test",
    instance_offering_uuid="xxx",
    image_uuid="xxx",
    l3_network_uuids=["xxx"]
)
```

Java SDK和Go SDK使用方式类似，具体参考官方文档。"""},
    ]


def _generate_networking_docs() -> list[dict]:
    return [
        {"title": "ZStack扁平网络详解",
         "content": """扁平网络模式：
云主机直接使用物理网络IP，与物理网络在同一广播域。

特点：
- 配置简单，网络性能好
- 云主机可直接被外部访问
- 不提供网络隔离
- 适合小规模或测试环境

配置步骤：
1. 识别物理机上的业务网口（如eth1）
2. 创建L2NoVlanNetwork，指定物理接口
3. 创建L3Network，配置IP Range
4. 添加DNS
5. 挂载到Cluster

注意：确保物理机网口已配置好且能联通。"""},
        {"title": "ZStack VPC网络详解",
         "content": """VPC（虚拟私有云）网络：
提供逻辑隔离的虚拟网络环境。

架构：
- 每个VPC拥有独立的虚拟路由器
- VPC内部使用私有IP地址段
- 通过SNAT访问外网
- 通过EIP/端口转发提供外部访问

网络服务：
- SNAT：源地址转换，云主机主动访问外网
- EIP：弹性IP，将公网IP绑定到云主机
- 端口转发：将公网端口映射到内网
- 负载均衡：多云主机负载分发
- IPsec VPN：站点到站点VPN连接

底层实现：VXLAN封装，支持跨物理机通信。"""},
        {"title": "ZStack安全组配置",
         "content": """安全组功能：
通过iptables规则控制云主机的入站和出站流量。

默认规则：
- 同安全组内云主机互通
- 入站流量默认拒绝
- 出站流量默认允许

配置示例：
1. 创建安全组
2. 添加规则：
   - 允许SSH：TCP 22 入站
   - 允许HTTP：TCP 80 入站
   - 允许ICMP：ICMP 入站
3. 将安全组绑定到云主机网卡

最佳实践：
- 按服务类型创建安全组（Web/DB/App）
- 最小权限原则
- 定期审查规则"""},
        {"title": "ZStack网络服务Provider",
         "content": """ZStack网络服务由不同Provider提供：

虚拟路由器(VirtualRouter)：
- 提供DHCP、DNS、SNAT等基础服务
- 以云主机形式运行，自动管理

安全组(SecurityGroup)：
- 基于iptables的流量控制
- 分布式实现，规则下发到各物理机

扁平网络Provider：
- DHCP服务通过dnsmasq实现
- 直接在物理机上提供网络服务

VPC Router：
- 提供完整的VPC网络服务
- 支持HA双活部署"""},
        {"title": "ZStack SDN网络",
         "content": """ZStack软件定义网络(SDN)：
使用VXLAN技术实现大规模租户网络隔离。

VXLAN网络架构：
- 使用UDP封装二层帧，支持跨三层网络通信
- VNI(VXLAN Network Identifier)提供隔离
- VTEP(VXLAN Tunnel End Point)在物理机上创建

配置要求：
1. 物理网络需支持大MTU(推荐1600+)
2. 物理交换机放通UDP 4789端口
3. 物理机间三层可达

ZStack简化了VXLAN的管理：
- 自动创建和管理VTEP
- VNI池化管理
- 与VPC网络无缝集成"""},
    ]


def _generate_storage_docs() -> list[dict]:
    return [
        {"title": "ZStack本地存储方案",
         "content": """本地存储(LocalStorage)：
使用物理机本地磁盘作为云主机存储。

特点：
- 配置简单，无需额外存储设备
- IO性能好（直接使用本地磁盘）
- 不支持在线迁移
- 物理机故障时数据可能丢失

适用场景：
- 测试环境
- 无状态应用
- 成本敏感场景

配置：在添加主存储时选择LocalStorage类型，指定存储路径。
默认路径：/zstack_ps"""},
        {"title": "ZStack Ceph存储方案",
         "content": """Ceph分布式存储：
推荐的生产环境存储方案。

优势：
- 高可靠：默认三副本
- 高扩展：线性扩展容量和性能
- 支持在线迁移、快照、克隆
- 支持增量备份

ZStack Ceph架构：
- 主存储(PrimaryStorage)：使用RBD存储云盘
- 镜像服务器(BackupStorage)：使用RBD或RGW存储镜像
- 支持快照回滚、镜像快速克隆

性能优化：
- 使用SSD作为Journal/WAL/DB
- 合理规划PG数量
- 启用RBD缓存
- 使用万兆网络"""},
        {"title": "ZStack共享块存储方案",
         "content": """SharedBlock存储：
通过共享块设备（iSCSI/FC LUN）提供存储。

特点：
- 利用企业级SAN存储能力
- 支持在线迁移
- 适合已有SAN设备的用户
- 需要文件系统管理（使用LVM）

架构：
- 共享LUN挂载到所有计算节点
- 使用Sanlock实现分布式锁
- LVM管理逻辑卷

配置步骤：
1. 在SAN存储上创建LUN
2. 将LUN映射到所有计算节点
3. 在ZStack中添加SharedBlock存储
4. 指定共享块设备路径"""},
        {"title": "ZStack存储性能优化",
         "content": """存储性能优化建议：

物理层：
1. 使用NVMe SSD提供高IOPS
2. 网络使用25G/100G
3. RAID配置根据场景选择

Ceph优化：
1. OSD使用独立SSD
2. 调整osd_op_threads
3. 启用RBD cache
4. 合理设置PG数量

本地存储优化：
1. 使用XFS文件系统
2. 启用discard/trim
3. 适当调整IO调度器

云主机侧：
1. 使用virtio-blk或virtio-scsi驱动
2. 启用缓存模式(writeback)
3. 使用多队列virtio"""},
        {"title": "ZStack云盘管理",
         "content": """云盘管理操作：

创建云盘：
- 系统盘：创建云主机时自动从镜像创建
- 数据盘：独立创建后挂载到云主机

云盘操作：
- 挂载/卸载：在线或离线挂载到云主机
- 扩容：在线扩容云盘大小
- 快照：创建时间点快照
- 克隆：从快照创建新云盘
- 备份：将云盘备份到镜像服务器

最佳实践：
- 数据盘与系统盘分离
- 定期创建快照
- 重要数据定期备份
- 监控云盘IO性能"""},
    ]


def _generate_compute_docs() -> list[dict]:
    return [
        {"title": "ZStack云主机生命周期",
         "content": """云主机状态机：
Created → Starting → Running → Stopping → Stopped
Running → Migrating → Running (迁移)
Running → Pausing → Paused → Resuming → Running
Stopped → Destroying → Destroyed → Expunging → Expunged

主要操作：
- 创建：选择镜像、规格、网络
- 启动/停止：电源管理
- 重启：软重启或硬重启
- 暂停/恢复：暂时冻结
- 迁移：在线或离线迁移到其他物理机
- 删除：放入回收站（软删除）
- 彻底删除：从系统中永久删除

回收站机制：删除的云主机默认保留24小时，可恢复。"""},
        {"title": "ZStack计算规格管理",
         "content": """计算规格(InstanceOffering)定义云主机的计算资源：
- CPU核数
- 内存大小
- 磁盘带宽限制
- 网络带宽限制

创建计算规格：
zstack-cli CreateInstanceOffering name=standard cpuNum=2 memorySize=4294967296

预设规格建议：
- 微型：1C/1G - 测试/开发
- 小型：2C/4G - 轻量应用
- 中型：4C/8G - 标准应用
- 大型：8C/16G - 数据库/中间件
- 超大型：16C/32G - 大型应用

支持在线变配：运行中修改CPU/内存。"""},
        {"title": "ZStack GPU虚拟化",
         "content": """ZStack支持GPU直通和vGPU：

GPU直通(Passthrough)：
- 将整块GPU分配给一个云主机
- 性能无损失
- 每块GPU只能分配给一个云主机

vGPU(虚拟化GPU)：
- 将一块GPU虚拟化为多个vGPU
- 多个云主机共享物理GPU
- 需要NVIDIA GRID驱动
- 支持NVIDIA Tesla/Quadro系列

应用场景：
- AI/ML训练和推理
- 图形渲染和设计
- 视频处理
- 云桌面(VDI)"""},
        {"title": "ZStack亲和性和反亲和性",
         "content": """亲和组(Affinity Group)：

亲和性(Affinity)：
- 将指定云主机调度到同一物理机
- 场景：需要低延迟通信的应用

反亲和性(Anti-Affinity)：
- 将指定云主机调度到不同物理机
- 场景：高可用部署，避免单点故障

配置方式：
1. 创建亲和组
2. 将云主机加入亲和组
3. 创建或迁移时自动按规则调度

最佳实践：
- 数据库主从使用反亲和性
- Web集群使用反亲和性
- 配套服务使用亲和性"""},
        {"title": "ZStack镜像管理",
         "content": """镜像管理：

支持的镜像格式：
- qcow2：推荐，支持快照和瘦配置
- raw：性能好但占用空间大
- vmdk：VMware格式，自动转换
- iso：用于安装操作系统

镜像来源：
1. 上传本地文件
2. 从URL下载
3. 从云主机创建（根云盘镜像）
4. 从快照创建

镜像优化：
- 安装virtio驱动
- 安装cloud-init
- 清理日志和临时文件
- 压缩qcow2：qemu-img convert -c

镜像分发：
- 上传到镜像服务器后自动分发
- 创建云主机时按需下载到主存储"""},
    ]


def _generate_security_docs() -> list[dict]:
    return [
        {"title": "ZStack安全最佳实践",
         "content": """安全配置建议：

账户安全：
1. 修改默认admin密码
2. 启用密码复杂度策略
3. 创建独立运维账户
4. 定期轮换密码
5. 启用Session超时

网络安全：
1. 管理网络与业务网络隔离
2. 使用安全组控制流量
3. 启用VPC网络隔离
4. 配置ACL规则

系统安全：
1. 及时更新系统补丁
2. 关闭不必要的端口
3. 启用审计日志
4. 监控异常登录

数据安全：
1. 启用存储加密
2. 定期备份
3. 备份加密存储"""},
        {"title": "ZStack多租户权限管理",
         "content": """ZStack多租户模型：

账户层次：
- 管理员(Admin)：最高权限
- 普通账户(Account)：租户隔离
- 用户(User)：账户下的子用户

权限控制：
- 基于策略(Policy)的权限管理
- 支持细粒度API权限控制
- 资源配额(Quota)限制

配额管理：
- CPU配额：限制可用CPU总数
- 内存配额：限制可用内存总量
- 存储配额：限制云盘总容量
- 网络配额：限制可用IP数量

最佳实践：
- 按部门或项目创建账户
- 设置合理的资源配额
- 最小权限原则分配策略"""},
        {"title": "ZStack审计日志",
         "content": """审计日志功能：

记录内容：
- 所有API调用
- 操作人和来源IP
- 操作时间和结果
- 资源变更详情

查询审计日志：
zstack-cli QueryEvent

日志保留：
- 默认保留30天
- 可配置保留期限
- 支持导出为CSV

合规建议：
- 启用所有审计日志
- 定期归档审计日志
- 配置异常操作告警
- 遵循等保要求"""},
    ]


def _generate_operations_docs() -> list[dict]:
    return [
        {"title": "ZStack日常运维手册",
         "content": """日常运维检查项：

每日检查：
1. 管理节点状态和日志
2. 物理机连接状态
3. 存储使用率
4. 网络连通性
5. 告警信息

每周检查：
1. 系统性能趋势
2. 资源使用率趋势
3. 备份完整性验证
4. 安全事件审查

每月检查：
1. 容量规划评审
2. 性能基线对比
3. 安全策略审查
4. 系统更新评估

运维工具：
- zstack-ctl：管理节点管理工具
- zstack-cli：命令行管理工具
- 管理UI：Web界面"""},
        {"title": "ZStack监控告警配置",
         "content": """监控系统配置：

ZStack内置监控：
- 物理机CPU/内存/磁盘/网络使用率
- 云主机资源使用率
- 存储容量和IOPS
- 网络流量

告警配置：
1. 创建告警规则
2. 设置告警条件和阈值
3. 配置通知方式（邮件/钉钉/Webhook）

推荐告警阈值：
- CPU使用率 > 80%
- 内存使用率 > 85%
- 存储使用率 > 80%
- 物理机断连

外部监控集成：
- 支持Prometheus指标导出
- Grafana仪表板模板
- 支持SNMP"""},
        {"title": "ZStack容量规划指南",
         "content": """容量规划方法：

计算资源规划：
- 超分比：CPU 1:4~1:8，内存 1:1~1:1.5
- 预留：物理机CPU/内存预留20%给宿主机系统
- HA预留：至少预留一台物理机容量用于HA

存储规划：
- 精简配置(Thin)实际使用约为分配的30-50%
- 快照空间预留30%
- Ceph三副本需要3倍原始容量

网络规划：
- 管理网络：千兆足够
- 存储网络：万兆推荐
- 业务网络：根据业务需求

增长预测：
- 基于历史使用率趋势
- 考虑业务增长计划
- 建议保持30%余量"""},
        {"title": "ZStack灾难恢复流程",
         "content": """灾难恢复方案：

管理节点故障恢复：
1. HA自动切换到备节点
2. 如果双节点都故障：
   a. 恢复数据库
   b. 重新部署管理节点
   c. 指向已有数据库

计算节点故障恢复：
1. HA自动迁移云主机到健康节点
2. 修复或替换故障节点
3. 重新添加到集群

存储故障恢复：
1. Ceph：依赖副本机制自动恢复
2. 本地存储：从备份恢复
3. SAN：依赖存储设备冗余

完全灾难恢复：
1. 恢复数据库备份
2. 重新部署管理节点
3. 确认存储数据完整
4. 重新连接计算节点
5. 验证云主机状态"""},
        {"title": "ZStack常用运维命令",
         "content": """管理节点命令：
- 启动：zstack-ctl start
- 停止：zstack-ctl stop
- 重启：zstack-ctl restart
- 状态：zstack-ctl status
- 升级：zstack-ctl upgrade
- 查看日志：zstack-ctl log
- 部署数据库：zstack-ctl deploydb
- 配置管理：zstack-ctl configure

KVM Agent命令：
- 重启Agent：systemctl restart zstack-kvmagent
- 查看日志：tail -f /var/log/zstack/zstack-kvmagent.log

数据库操作：
- 备份：mysqldump -u root zstack > backup.sql
- 恢复：mysql -u root zstack < backup.sql
- 查看大小：mysql -e "SELECT table_schema, SUM(data_length+index_length)/1024/1024 as 'Size(MB)' FROM information_schema.tables GROUP BY table_schema"

Ceph操作：
- 状态：ceph -s
- 空间：ceph df
- OSD状态：ceph osd tree"""},
    ]


def bootstrap_knowledge_base(
    seed_dir: str = None,
    target_count: int = None,
) -> BootstrapResponse:
    """
    Bootstrap the knowledge base with initial data.

    1. Load seed files from disk
    2. Generate synthetic data if needed
    3. Chunk, embed, and store until target_count reached
    """
    settings = get_settings()
    seed_dir = seed_dir or settings.seed_data_dir
    target_count = target_count or settings.bootstrap_record_count

    response = BootstrapResponse()
    start_time = time.time()

    try:
        store = get_vector_store()
        current_count = store.count()

        if current_count >= target_count:
            response.total_records = current_count
            response.metadata = {"message": f"Knowledge base already has {current_count} records (target: {target_count})."}
            response.duration_seconds = time.time() - start_time
            return response

        # Load seed files
        records = load_seed_files(seed_dir)
        logger.info(f"Loaded {len(records)} records from seed files")

        # Generate synthetic data if needed
        synthetic = generate_synthetic_seed_data()
        records.extend(synthetic)
        logger.info(f"Generated {len(synthetic)} synthetic records")

        response.total_records = len(records)

        # Chunk all records
        all_chunks = []
        for record in records:
            chunks = chunk_text(
                text=record["content"],
                source=record.get("source", "seed"),
                title=record.get("title", ""),
                document_type=record.get("document_type", "seed"),
                source_type="seed",
            )
            all_chunks.extend(chunks)

        # Limit to target count
        if len(all_chunks) > target_count:
            all_chunks = all_chunks[:target_count]

        if not all_chunks:
            response.errors.append("No chunks generated from seed data")
            response.duration_seconds = time.time() - start_time
            return response

        # Generate embeddings in batches
        embedding_service = get_embedding_service()
        texts = [c["content"] for c in all_chunks]
        embeddings = embedding_service.embed_texts(texts)

        # Store
        ids = [c["id"] for c in all_chunks]
        metadatas = [c["metadata"] for c in all_chunks]
        added = store.add_documents(ids, texts, embeddings, metadatas)

        response.chunks_created = added
        response.duration_seconds = time.time() - start_time

        logger.info(
            f"Bootstrap complete: {added} chunks added in {response.duration_seconds:.1f}s "
            f"(total in DB: {store.count()})"
        )

    except Exception as e:
        logger.error(f"Bootstrap error: {e}")
        response.errors.append(str(e))
        response.duration_seconds = time.time() - start_time

    return response
