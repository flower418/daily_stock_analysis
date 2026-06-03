import type React from 'react';
import { useEffect, useMemo, useState } from 'react';
import { Cloud, ExternalLink, GitBranch, Play, RefreshCw } from 'lucide-react';
import { systemConfigApi } from '../api/systemConfig';
import { getParsedApiError, type ParsedApiError } from '../api/error';
import { ApiErrorAlert, Button, Card, Select } from '../components/common';
import type { GitHubActionsMode, GitHubActionsRunSummary, GitHubActionsStatusResponse } from '../types/systemConfig';

const MODE_OPTIONS: Array<{ label: string; value: GitHubActionsMode }> = [
  { label: '完整分析', value: 'full' },
  { label: '仅大盘复盘', value: 'market-only' },
  { label: '仅股票分析', value: 'stocks-only' },
];

function formatDateTime(value?: string | null) {
  if (!value) {
    return '-';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getRunTone(run: GitHubActionsRunSummary) {
  if (run.status !== 'completed') {
    return 'border-cyan/30 bg-cyan/8 text-cyan';
  }
  if (run.conclusion === 'success') {
    return 'border-emerald/30 bg-emerald/8 text-emerald';
  }
  if (run.conclusion === 'failure' || run.conclusion === 'cancelled') {
    return 'border-danger/35 bg-danger/10 text-danger';
  }
  return 'border-border bg-muted/20 text-secondary-text';
}

const CloudActionsPage: React.FC = () => {
  const [status, setStatus] = useState<GitHubActionsStatusResponse | null>(null);
  const [loadError, setLoadError] = useState<ParsedApiError | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDispatching, setIsDispatching] = useState(false);
  const [mode, setMode] = useState<GitHubActionsMode>('full');
  const [forceRun, setForceRun] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    document.title = '云端任务 - DSA';
  }, []);

  const latestRun = useMemo(() => status?.runs?.[0], [status]);

  const load = async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const payload = await systemConfigApi.getGitHubActionsStatus();
      setStatus(payload);
    } catch (error) {
      setLoadError(getParsedApiError(error));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const dispatchWorkflow = async () => {
    setIsDispatching(true);
    setLoadError(null);
    setSuccessMessage('');
    try {
      await systemConfigApi.dispatchGitHubActions({ mode, forceRun });
      setSuccessMessage('已提交云端分析任务，GitHub Actions 通常会在数秒内创建运行记录。');
      window.setTimeout(() => {
        void load();
      }, 2500);
    } catch (error) {
      setLoadError(getParsedApiError(error));
    } finally {
      setIsDispatching(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-cyan/20 bg-cyan/10 text-cyan">
              <Cloud className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-foreground">云端任务</h1>
              <p className="mt-1 text-sm text-secondary-text">在本地桌面端查看并触发 GitHub Actions 每日分析。</p>
            </div>
          </div>
        </div>
        <Button variant="secondary" onClick={() => void load()} isLoading={isLoading} loadingText="刷新中">
          <RefreshCw className="h-4 w-4" />
          刷新
        </Button>
      </div>

      {loadError ? <ApiErrorAlert error={loadError} /> : null}

      {successMessage ? (
        <div className="rounded-xl border border-emerald/30 bg-emerald/10 px-4 py-3 text-sm text-emerald">
          {successMessage}
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
        <Card title="GitHub Actions" subtitle={status?.repo || 'Cloud workflow'} padding="lg">
          {status ? (
            <div className="space-y-4">
              <div className="grid gap-3 md:grid-cols-3">
                <div className="rounded-xl border border-border/70 bg-muted/20 p-3">
                  <p className="text-xs text-secondary-text">Workflow</p>
                  <p className="mt-1 truncate text-sm font-medium text-foreground">{status.workflow}</p>
                </div>
                <div className="rounded-xl border border-border/70 bg-muted/20 p-3">
                  <p className="text-xs text-secondary-text">Branch</p>
                  <p className="mt-1 flex items-center gap-2 truncate text-sm font-medium text-foreground">
                    <GitBranch className="h-4 w-4 text-secondary-text" />
                    {status.branch}
                  </p>
                </div>
                <div className="rounded-xl border border-border/70 bg-muted/20 p-3">
                  <p className="text-xs text-secondary-text">State</p>
                  <p className="mt-1 text-sm font-medium text-foreground">{status.workflowState || '-'}</p>
                </div>
              </div>

              {latestRun ? (
                <div className="rounded-xl border border-border/70 bg-card/70 p-4">
                  <p className="text-xs text-secondary-text">最近一次运行</p>
                  <div className="mt-2 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                    <div>
                      <p className="text-sm font-medium text-foreground">{latestRun.displayTitle || latestRun.name}</p>
                      <p className="mt-1 text-xs text-secondary-text">
                        {latestRun.event} · {formatDateTime(latestRun.runStartedAt || latestRun.createdAt)}
                      </p>
                    </div>
                    <span className={`inline-flex w-fit items-center rounded-full border px-3 py-1 text-xs ${getRunTone(latestRun)}`}>
                      {latestRun.status}{latestRun.conclusion ? ` / ${latestRun.conclusion}` : ''}
                    </span>
                  </div>
                </div>
              ) : null}

              <div className="space-y-2">
                {status.runs.map((run) => (
                  <div key={run.id} className="flex flex-col gap-2 rounded-xl border border-border/60 bg-muted/10 p-3 md:flex-row md:items-center md:justify-between">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-foreground">{run.displayTitle || run.name}</p>
                      <p className="mt-1 text-xs text-secondary-text">
                        {run.event} · {formatDateTime(run.runStartedAt || run.createdAt)}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs ${getRunTone(run)}`}>
                        {run.status}{run.conclusion ? ` / ${run.conclusion}` : ''}
                      </span>
                      {run.htmlUrl ? (
                        <a className="text-secondary-text hover:text-foreground" href={run.htmlUrl} target="_blank" rel="noreferrer" aria-label="打开运行记录">
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-border/70 bg-muted/20 p-4 text-sm text-secondary-text">
              在设置页填写 `GITHUB_ACTIONS_REPO`、`GITHUB_ACTIONS_TOKEN`、`GITHUB_ACTIONS_WORKFLOW` 后即可连接云端任务。
            </div>
          )}
        </Card>

        <Card title="触发分析" subtitle="Workflow dispatch" padding="lg">
          <div className="space-y-4">
            <label className="block text-sm">
              <span className="mb-2 block text-secondary-text">运行模式</span>
              <Select
                value={mode}
                onChange={(value) => setMode(value as GitHubActionsMode)}
                options={MODE_OPTIONS}
              />
            </label>
            <label className="flex items-center gap-3 rounded-xl border border-border/70 bg-muted/15 p-3 text-sm text-foreground">
              <input
                type="checkbox"
                checked={forceRun}
                onChange={(event) => setForceRun(event.target.checked)}
                className="h-4 w-4 accent-cyan"
              />
              跳过交易日检查
            </label>
            <Button
              className="w-full"
              onClick={() => void dispatchWorkflow()}
              isLoading={isDispatching}
              loadingText="提交中"
            >
              <Play className="h-4 w-4" />
              运行云端分析
            </Button>
            <p className="text-xs leading-5 text-secondary-text">
              该操作会调用 GitHub `workflow_dispatch`。任务仍在 GitHub runner 上执行，使用 GitHub Secrets / Variables 中的模型、股票和通知配置。
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default CloudActionsPage;
