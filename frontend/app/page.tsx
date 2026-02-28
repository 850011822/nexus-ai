'use client'

import { useState, useEffect, useRef } from 'react'
import { Terminal, Activity, Cpu, Play, Square, Plus, Brain, Users, Zap, Clock } from 'lucide-react'

// 类型定义
interface SystemStatus {
  status: string
  uptime: number
  active_agents: number
  tasks_completed: number
  current_task: string | null
}

interface Task {
  id: number
  name: string
  status: string
  created_at: string
  completed_at: string | null
}

interface LogMessage {
  level: string
  message: string
  timestamp: string
}

export default function Dashboard() {
  // 状态
  const [status, setStatus] = useState<SystemStatus>({
    status: 'stopped',
    uptime: 0,
    active_agents: 0,
    tasks_completed: 0,
    current_task: null
  })
  const [tasks, setTasks] = useState<Task[]>([])
  const [logs, setLogs] = useState<LogMessage[]>([])
  const [newTask, setNewTask] = useState('')
  const [loading, setLoading] = useState(false)
  const [connected, setConnected] = useState(false)
  const logsEndRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  // WebSocket连接
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws')
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'log') {
          setLogs(prev => [...prev.slice(-100), {
            level: data.level,
            message: data.message,
            timestamp: data.timestamp
          }])
        } else if (data.type === 'task_started' || data.type === 'task_completed') {
          fetchStatus()
          fetchTasks()
        }
      } catch (e) {
        console.error('Failed to parse message:', e)
      }
    }

    ws.onclose = () => {
      setConnected(false)
    }

    return () => {
      ws.close()
    }
  }, [])

  // 自动滚动日志
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  // 获取状态
  const fetchStatus = async () => {
    try {
      const res = await fetch('http://localhost:8000/status')
      const data = await res.json()
      setStatus(data)
    } catch (e) {
      console.error('Failed to fetch status:', e)
    }
  }

  // 获取任务
  const fetchTasks = async () => {
    try {
      const res = await fetch('http://localhost:8000/tasks')
      const data = await res.json()
      setTasks(data)
    } catch (e) {
      console.error('Failed to fetch tasks:', e)
    }
  }

  // 获取日志
  const fetchLogs = async () => {
    try {
      const res = await fetch('http://localhost:8000/logs?limit=50')
      const data = await res.json()
      setLogs(data.reverse())
    } catch (e) {
      console.error('Failed to fetch logs:', e)
    }
  }

  // 定时刷新
  useEffect(() => {
    fetchStatus()
    fetchTasks()
    fetchLogs()

    const interval = setInterval(() => {
      fetchStatus()
      fetchTasks()
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  // 启动系统
  const startSystem = async () => {
    setLoading(true)
    try {
      await fetch('http://localhost:8000/start', { method: 'POST' })
      fetchStatus()
    } catch (e) {
      console.error('Failed to start:', e)
    }
    setLoading(false)
  }

  // 停止系统
  const stopSystem = async () => {
    setLoading(true)
    try {
      await fetch('http://localhost:8000/stop', { method: 'POST' })
      fetchStatus()
    } catch (e) {
      console.error('Failed to stop:', e)
    }
    setLoading(false)
  }

  // 创建任务
  const createTask = async () => {
    if (!newTask.trim()) return

    setLoading(true)
    try {
      await fetch('http://localhost:8000/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: newTask, mode: 'auto' })
      })
      setNewTask('')
      fetchTasks()
    } catch (e) {
      console.error('Failed to create task:', e)
    }
    setLoading(false)
  }

  // 格式化时间
  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    return `${hours}h ${minutes}m ${secs}s`
  }

  return (
    <div className="min-h-screen bg-[#0B1120] text-white">
      {/* Header */}
      <header className="border-b border-gray-800 bg-[#0F172A]">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Brain className="h-8 w-8 text-blue-500" />
              <h1 className="text-2xl font-bold">Nexus-AI</h1>
              <span className="text-sm text-gray-400">自主运营系统</span>
            </div>
            <div className="flex items-center space-x-4">
              <div className={`flex items-center space-x-2 ${connected ? 'text-green-500' : 'text-red-500'}`}>
                <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm">{connected ? '已连接' : '未连接'}</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">系统状态</p>
                <p className={`text-2xl font-bold mt-1 ${status.status === 'running' ? 'text-green-500' : 'text-gray-500'}`}>
                  {status.status === 'running' ? '运行中' : '已停止'}
                </p>
              </div>
              <Activity className="h-8 w-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">运行时间</p>
                <p className="text-2xl font-bold mt-1">{formatUptime(status.uptime)}</p>
              </div>
              <Clock className="h-8 w-8 text-purple-500" />
            </div>
          </div>

          <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">活跃Agent</p>
                <p className="text-2xl font-bold mt-1">{status.active_agents}</p>
              </div>
              <Users className="h-8 w-8 text-green-500" />
            </div>
          </div>

          <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">完成任务</p>
                <p className="text-2xl font-bold mt-1">{status.tasks_completed}</p>
              </div>
              <Zap className="h-8 w-8 text-yellow-500" />
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Tasks & Controls */}
          <div className="lg:col-span-2 space-y-6">
            {/* Control Panel */}
            <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-800">
              <h2 className="text-xl font-bold mb-4 flex items-center">
                <Cpu className="h-5 w-5 mr-2 text-blue-500" />
                控制面板
              </h2>
              <div className="flex space-x-4">
                <button
                  onClick={startSystem}
                  disabled={loading || status.status === 'running'}
                  className="flex items-center px-6 py-3 bg-green-600 hover:bg-green-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  <Play className="h-5 w-5 mr-2" />
                  启动系统
                </button>
                <button
                  onClick={stopSystem}
                  disabled={loading || status.status === 'stopped'}
                  className="flex items-center px-6 py-3 bg-red-600 hover:bg-red-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  <Square className="h-5 w-5 mr-2" />
                  停止系统
                </button>
              </div>

              {/* New Task Input */}
              <div className="mt-6">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={newTask}
                    onChange={(e) => setNewTask(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && createTask()}
                    placeholder="输入新任务..."
                    className="flex-1 px-4 py-3 bg-[#0B1120] border border-gray-700 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                  <button
                    onClick={createTask}
                    disabled={loading || !newTask.trim()}
                    className="flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition"
                  >
                    <Plus className="h-5 w-5 mr-2" />
                    添加任务
                  </button>
                </div>
              </div>
            </div>

            {/* Tasks List */}
            <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-800">
              <h2 className="text-xl font-bold mb-4 flex items-center">
                <Activity className="h-5 w-5 mr-2 text-blue-500" />
                任务列表
              </h2>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {tasks.length === 0 ? (
                  <p className="text-gray-400 text-center py-8">暂无任务</p>
                ) : (
                  tasks.map((task) => (
                    <div
                      key={task.id}
                      className="flex items-center justify-between p-4 bg-[#0B1120] rounded-lg border border-gray-700"
                    >
                      <div>
                        <p className="font-medium">{task.name}</p>
                        <p className="text-sm text-gray-400">
                          {task.created_at}
                        </p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-sm ${
                        task.status === 'completed'
                          ? 'bg-green-900 text-green-300'
                          : task.status === 'running'
                          ? 'bg-blue-900 text-blue-300'
                          : 'bg-red-900 text-red-300'
                      }`}>
                        {task.status === 'completed' ? '已完成' : task.status === 'running' ? '进行中' : '失败'}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Logs */}
          <div className="lg:col-span-1">
            <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-800 h-full">
              <h2 className="text-xl font-bold mb-4 flex items-center">
                <Terminal className="h-5 w-5 mr-2 text-blue-500" />
                实时日志
              </h2>
              <div className="bg-[#0B1120] rounded-lg p-4 h-[500px] overflow-y-auto font-mono text-sm">
                {logs.length === 0 ? (
                  <p className="text-gray-500">等待日志...</p>
                ) : (
                  logs.map((log, i) => (
                    <div key={i} className="mb-2">
                      <span className="text-gray-500">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                      <span className={`ml-2 ${
                        log.level === 'error' ? 'text-red-400' :
                        log.level === 'warning' ? 'text-yellow-400' :
                        'text-green-400'
                      }`}>
                        [{log.level.toUpperCase()}]
                      </span>
                      <span className="ml-2 text-gray-300">{log.message}</span>
                    </div>
                  ))
                )}
                <div ref={logsEndRef} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
