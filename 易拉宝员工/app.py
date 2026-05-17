import streamlit as st
import os
from pathlib import Path
from datetime import datetime
import time
from PIL import Image

from runninghub_client import RunningHubClient
from workflow_config import WorkflowConfig
from test_recorder import TestRecorder


# 页面配置
st.set_page_config(
    page_title="Running Hub 工作流测试工具",
    page_icon="🎨",
    layout="wide"
)

# 初始化session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'client' not in st.session_state:
    st.session_state.client = None
if 'current_task_id' not in st.session_state:
    st.session_state.current_task_id = None
if 'uploaded_image_path' not in st.session_state:
    st.session_state.uploaded_image_path = None

# 初始化管理器
workflow_config = WorkflowConfig()
test_recorder = TestRecorder()


def main():
    st.title("🎨 Running Hub 工作流测试工具")
    st.markdown("---")

    # 侧边栏
    with st.sidebar:
        st.header("⚙️ API 配置")

        api_key = st.text_input(
            "API Key",
            value=st.session_state.api_key,
            type="password",
            help="输入你的 Running Hub API Key"
        )

        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
            if api_key:
                st.session_state.client = RunningHubClient(api_key)

        if st.button("🔌 测试连接"):
            if not st.session_state.client:
                st.error("请先输入 API Key")
            else:
                with st.spinner("测试连接中..."):
                    if st.session_state.client.test_connection():
                        st.success("✅ 连接成功!")
                    else:
                        st.error("❌ 连接失败,请检查 API Key")

        st.markdown("---")
        st.header("📋 工作流管理")

        # 工作流选择
        workflows = workflow_config.get_all_workflows()
        if workflows:
            workflow_names = [f"{wf['name']} ({wf['id']})" for wf in workflows]
            selected_idx = st.selectbox(
                "选择工作流",
                range(len(workflows)),
                format_func=lambda i: workflow_names[i]
            )
            selected_workflow = workflows[selected_idx]
        else:
            st.info("还没有添加工作流")
            selected_workflow = None

        # 添加新工作流
        with st.expander("➕ 添加新工作流"):
            add_workflow_form()

        # 编辑当前工作流
        if selected_workflow:
            with st.expander("✏️ 编辑当前工作流"):
                edit_workflow_form(selected_workflow)

        st.markdown("---")

        # 统计信息
        stats = test_recorder.get_test_statistics()
        st.metric("总测试次数", stats['total_tests'])
        col1, col2 = st.columns(2)
        with col1:
            st.metric("成功", stats['success_count'])
        with col2:
            st.metric("失败", stats['failed_count'])

    # 主区域 - 标签页
    if not st.session_state.client:
        st.warning("⚠️ 请先在左侧配置 API Key")
        return

    if not selected_workflow:
        st.info("👈 请先在左侧添加工作流")
        return

    tab1, tab2, tab3 = st.tabs(["🚀 测试工作流", "📊 测试结果", "📜 历史记录"])

    with tab1:
        test_workflow_tab(selected_workflow)

    with tab2:
        results_tab()

    with tab3:
        history_tab(selected_workflow)


def add_workflow_form():
    """添加工作流表单"""
    with st.form("add_workflow_form"):
        workflow_id = st.text_input("工作流 ID", help="例如: 1991530280437628929")
        workflow_name = st.text_input("工作流名称", help="例如: 易拉宝设计A")
        workflow_desc = st.text_area("描述", help="简单描述这个工作流的用途")
        workflow_type = st.selectbox("类型", ["workflow", "ai-app"])

        submitted = st.form_submit_button("添加")
        if submitted:
            if not workflow_id or not workflow_name:
                st.error("请填写工作流 ID 和名称")
            else:
                if workflow_config.add_workflow(
                    workflow_id, workflow_name, workflow_desc, workflow_type
                ):
                    st.success(f"✅ 已添加工作流: {workflow_name}")
                    st.rerun()
                else:
                    st.error("添加失败,可能已存在相同ID的工作流")


def edit_workflow_form(workflow):
    """编辑工作流表单"""
    st.write(f"**工作流 ID:** {workflow['id']}")
    st.write(f"**类型:** {workflow['type']}")

    # 显示现有参数
    st.subheader("节点参数配置")
    node_template = workflow.get('node_info_template', [])

    if node_template:
        for idx, node in enumerate(node_template):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.text(f"节点: {node['nodeId']}")
            with col2:
                st.text(f"字段: {node['fieldName']}")
            with col3:
                if st.button("🗑️", key=f"del_{idx}"):
                    workflow_config.remove_node_info(
                        workflow['id'], node['nodeId'], node['fieldName']
                    )
                    st.rerun()
    else:
        st.info("此工作流暂无参数配置(nodeInfoList为空)")

    # 添加新参数
    st.subheader("添加节点参数")
    with st.form(f"add_node_{workflow['id']}"):
        col1, col2 = st.columns(2)
        with col1:
            node_id = st.text_input("节点 ID", help="例如: 25")
            field_name = st.text_input("字段名", help="例如: image")
        with col2:
            field_type = st.selectbox("字段类型", ["text", "image", "number"])
            description = st.text_input("描述", help="例如: 产品图片")

        submitted = st.form_submit_button("添加参数")
        if submitted:
            if node_id and field_name:
                workflow_config.add_node_info(
                    workflow['id'], node_id, field_name, field_type, description
                )
                st.success("✅ 已添加参数")
                st.rerun()


def test_workflow_tab(workflow):
    """测试工作流标签页"""
    st.header(f"测试: {workflow['name']}")
    st.write(f"**描述:** {workflow['description']}")
    st.write(f"**工作流ID:** {workflow['id']}")

    st.markdown("---")

    # 参数配置
    st.subheader("📝 参数配置")

    node_template = workflow.get('node_info_template', [])
    node_info_list = []

    if node_template:
        for node in node_template:
            st.write(f"**{node['description'] or node['fieldName']}**")

            if node['fieldType'] == 'image':
                # 图片上传
                uploaded_file = st.file_uploader(
                    f"上传图片 (节点{node['nodeId']})",
                    type=['png', 'jpg', 'jpeg'],
                    key=f"upload_{node['nodeId']}_{node['fieldName']}"
                )

                if uploaded_file:
                    # 保存临时文件
                    temp_dir = Path("temp_uploads")
                    temp_dir.mkdir(exist_ok=True)
                    temp_path = temp_dir / uploaded_file.name

                    with open(temp_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())

                    st.image(uploaded_file, width=200)

                    # 上传到Running Hub
                    if st.button(f"上传到 Running Hub", key=f"rh_upload_{node['nodeId']}"):
                        with st.spinner("上传中..."):
                            file_name = st.session_state.client.upload_image(str(temp_path))
                            if file_name:
                                st.success(f"✅ 上传成功: {file_name}")
                                node_info_list.append({
                                    "nodeId": node['nodeId'],
                                    "fieldName": node['fieldName'],
                                    "fieldValue": file_name,
                                    "description": node['description']
                                })
                            else:
                                st.error("上传失败")

            elif node['fieldType'] == 'number':
                value = st.number_input(
                    f"节点 {node['nodeId']} - {node['fieldName']}",
                    key=f"input_{node['nodeId']}_{node['fieldName']}"
                )
                if value:
                    node_info_list.append({
                        "nodeId": node['nodeId'],
                        "fieldName": node['fieldName'],
                        "fieldValue": str(value),
                        "description": node['description']
                    })

            else:  # text
                value = st.text_input(
                    f"节点 {node['nodeId']} - {node['fieldName']}",
                    key=f"input_{node['nodeId']}_{node['fieldName']}"
                )
                if value:
                    node_info_list.append({
                        "nodeId": node['nodeId'],
                        "fieldName": node['fieldName'],
                        "fieldValue": value,
                        "description": node['description']
                    })
    else:
        st.info("此工作流不需要参数,可以直接运行")

    st.markdown("---")

    # 提交按钮
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🚀 开始生成", type="primary", use_container_width=True):
            run_workflow(workflow, node_info_list)


def run_workflow(workflow, node_info_list):
    """运行工作流"""
    with st.spinner("🔄 提交任务中..."):
        result = st.session_state.client.start_workflow(
            workflow['id'],
            node_info_list,
            workflow_type=workflow['type']
        )

        if not result:
            st.error("❌ 提交失败")
            return

        task_id = result.get('taskId')
        status = result.get('status')

        st.success(f"✅ 任务已提交! Task ID: {task_id}")
        st.info(f"当前状态: {status}")

        # 保存到session state
        st.session_state.current_task_id = task_id

    # 自动轮询
    st.markdown("---")
    st.subheader("⏳ 等待结果...")

    progress_bar = st.progress(0)
    status_text = st.empty()

    max_wait = 600  # 10分钟
    poll_interval = 5
    elapsed = 0

    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval

        progress = min(elapsed / max_wait, 0.99)
        progress_bar.progress(progress)

        task_result = st.session_state.client.query_task(task_id)

        if not task_result:
            status_text.error("查询失败")
            break

        current_status = task_result.get('status')
        status_text.info(f"状态: {current_status} (已等待 {elapsed}秒)")

        if current_status == 'SUCCESS':
            progress_bar.progress(1.0)
            status_text.success("✅ 生成完成!")

            # 保存测试记录
            test_id = test_recorder.add_test_record(
                workflow['id'],
                workflow['name'],
                task_id,
                {"nodeInfoList": node_info_list},
                task_result.get('results', []),
                'SUCCESS',
                task_result.get('usage', {}).get('taskCostTime', ''),
                ""
            )

            # 显示结果
            display_results(task_result, test_id)
            break

        elif current_status == 'FAILED':
            status_text.error(f"❌ 生成失败: {task_result.get('errorMessage')}")

            # 保存失败记录
            test_recorder.add_test_record(
                workflow['id'],
                workflow['name'],
                task_id,
                {"nodeInfoList": node_info_list},
                [],
                'FAILED',
                "",
                task_result.get('errorMessage', '')
            )
            break


def display_results(task_result, test_id):
    """显示生成结果"""
    st.markdown("---")
    st.subheader("🎉 生成结果")

    results = task_result.get('results', [])

    if not results:
        st.warning("没有生成结果")
        return

    # 显示图片
    cols = st.columns(min(len(results), 3))
    for idx, result in enumerate(results):
        with cols[idx % 3]:
            image_url = result.get('url')
            if image_url:
                st.image(image_url, caption=f"结果 {idx + 1}")
                st.markdown(f"[下载图片]({image_url})")

                # 下载到本地
                if st.button(f"💾 保存到本地", key=f"save_{idx}"):
                    save_path = f"results/{test_id}/result_{idx}.{result.get('outputType', 'png')}"
                    if st.session_state.client.download_image(image_url, save_path):
                        st.success(f"已保存到: {save_path}")

    # 评分和备注
    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    with col1:
        rating = st.slider("评分", 1, 5, 3, key=f"rating_{test_id}")
        if st.button("保存评分"):
            test_recorder.update_rating(test_id, rating)
            st.success("✅ 已保存评分")

    with col2:
        notes = st.text_area("备注", key=f"notes_{test_id}")
        if st.button("保存备注"):
            test_recorder.update_notes(test_id, notes)
            st.success("✅ 已保存备注")


def results_tab():
    """结果展示标签页"""
    st.header("📊 当前任务结果")

    if not st.session_state.current_task_id:
        st.info("还没有运行任务")
        return

    task_id = st.session_state.current_task_id

    if st.button("🔄 刷新状态"):
        task_result = st.session_state.client.query_task(task_id)
        if task_result:
            st.json(task_result)
        else:
            st.error("查询失败")


def history_tab(workflow):
    """历史记录标签页"""
    st.header("📜 测试历史")

    # 筛选选项
    col1, col2 = st.columns([3, 1])
    with col1:
        show_all = st.checkbox("显示所有工作流的记录", value=False)
    with col2:
        if st.button("🔄 刷新"):
            st.rerun()

    # 获取记录
    if show_all:
        records = test_recorder.get_all_test_records()
    else:
        records = test_recorder.get_workflow_tests(workflow['id'])

    if not records:
        st.info("还没有测试记录")
        return

    # 按时间倒序
    records = sorted(records, key=lambda x: x['timestamp'], reverse=True)

    # 显示记录
    for record in records:
        with st.expander(
            f"🧪 {record['workflow_name']} - {record['timestamp'][:19]} - {record['status']}"
        ):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**测试ID:** {record['test_id']}")
                st.write(f"**任务ID:** {record['task_id']}")
            with col2:
                st.write(f"**状态:** {record['status']}")
                st.write(f"**耗时:** {record.get('cost_time', 'N/A')}")
            with col3:
                rating = record.get('rating', 0)
                st.write(f"**评分:** {'⭐' * rating if rating > 0 else '未评分'}")

            if record.get('notes'):
                st.write(f"**备注:** {record['notes']}")

            # 显示结果图片
            if record.get('results'):
                st.write("**生成结果:**")
                cols = st.columns(min(len(record['results']), 3))
                for idx, result in enumerate(record['results']):
                    with cols[idx % 3]:
                        if result.get('url'):
                            st.image(result['url'], width=200)

            # 删除按钮
            if st.button("🗑️ 删除此记录", key=f"del_record_{record['test_id']}"):
                if test_recorder.delete_test_record(record['test_id']):
                    st.success("已删除")
                    st.rerun()


if __name__ == "__main__":
    main()
