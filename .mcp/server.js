const express = require('express');
const bodyParser = require('body-parser');
const { execSync } = require('child_process');
const path = require('path');

const app = express();
app.use(bodyParser.json({ limit: '10mb' }));

const REPO_ROOT = path.resolve(__dirname, '..');

function git(cmd) {
  return execSync(`git ${cmd}`, { cwd: REPO_ROOT }).toString();
}

app.post('/precommit', (req, res) => {
  const { message } = req.body;
  if (!message) return res.status(400).send({ error: 'missing message' });
  try {
    git('add -A');
    const status = git('status --porcelain');
    if (status.trim()) {
      git(`commit -m "${message.replace(/"/g, '\\"')}"`);
      return res.send({ ok: true, committed: true });
    }
    return res.send({ ok: true, committed: false });
  } catch (e) {
    return res.status(500).send({ error: e.message });
  }
});

app.post('/apply', (req, res) => {
  const { filePath, content } = req.body;
  if (!filePath || typeof content !== 'string') return res.status(400).send({ error: 'invalid payload' });
  try {
    const full = path.join(REPO_ROOT, filePath);
    require('fs').writeFileSync(full, content, 'utf8');
    return res.send({ ok: true });
  } catch (e) {
    return res.status(500).send({ error: e.message });
  }
});

const PORT = process.env.PORT || 3040;
app.listen(PORT, () => console.log(`MCP server listening on ${PORT}`));
