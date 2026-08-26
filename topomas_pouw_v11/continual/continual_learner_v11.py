import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from collections import defaultdict
from typing import Dict, Any, List, Tuple, Callable
import random

class ExperienceReplay:
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.buffer = []
        self.position = 0

    def push(self, state, target):
        if len(self.buffer) < self.capacity:
            self.buffer.append(None)
        self.buffer[self.position] = (state, target)
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size: int):
        if len(self.buffer) == 0:
            return None
        batch = random.sample(self.buffer, min(batch_size, len(self.buffer)))
        states, targets = zip(*batch)
        return torch.stack(states), torch.stack(targets)

    def __len__(self):
        return len(self.buffer)

class ElasticWeightConsolidation:
    def __init__(self, model: nn.Module, importance: float = 1e3):
        self.model = model
        self.importance = importance
        self.fisher = defaultdict(float)
        self.optimal_params = {n: p.clone().detach() for n, p in model.named_parameters() if p.requires_grad}
        self._has_fisher = False

    def compute_fisher(
        self,
        reference_loader: DataLoader,
        criterion: Callable[[torch.Tensor, torch.Tensor], torch.Tensor],
        device: str = "cpu",
    ) -> Dict[str, torch.Tensor]:
        self.model.eval()
        fisher_new = defaultdict(float)

        for inputs, targets in reference_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = self.model(inputs)
            loss = criterion(outputs, targets)

            self.model.zero_grad()
            loss.backward(retain_graph=False)

            batch_size_actual = inputs.size(0)
            for name, param in self.model.named_parameters():
                if param.grad is None:
                    continue
                # E[g_i²] ≈ B * E[(grad_mean)²]  (correção por amostras)
                grad_sq = param.grad.detach().clone() ** 2 * batch_size_actual
                if name not in fisher_new:
                    fisher_new[name] = grad_sq
                else:
                    fisher_new[name] += grad_sq

        n_samples = len(reference_loader.dataset)
        for name in fisher_new:
            fisher_new[name] /= n_samples

        self.fisher = fisher_new
        self.optimal_params = {n: p.clone().detach() for n, p in self.model.named_parameters() if p.requires_grad}
        self._has_fisher = True
        return self.fisher

    def ewc_loss(self, device: str = "cpu") -> torch.Tensor:
        loss = torch.tensor(0.0, device=device)
        if not self._has_fisher:
            return loss

        for name, param in self.model.named_parameters():
            if name in self.fisher and param.requires_grad:
                optimal_param = self.optimal_params[name].to(device)
                fisher_val = self.fisher[name].to(device)
                loss += (fisher_val * (param - optimal_param) ** 2).sum()

        return loss * self.importance

class ContinualLearningAgent:
    name = "ContinualLearner_v11"

    def __init__(self, target_model: nn.Module, importance: float = 1e4, replay_capacity: int = 5000):
        self.target_model = target_model
        self.ewc = ElasticWeightConsolidation(target_model, importance=importance)
        self.replay_buffer = ExperienceReplay(capacity=replay_capacity)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.target_model.to(self.device)
        self.criterion = nn.MSELoss()

    def compute_fisher_on_reference(self, reference_data: List[Dict]):
        if not reference_data:
            return

        try:
            X = torch.stack([d["features"] for d in reference_data]).float()
            y = torch.stack([d["target"] for d in reference_data]).float()
            dataset = TensorDataset(X, y)
            loader = DataLoader(dataset, batch_size=32, shuffle=True)
            self.ewc.compute_fisher(loader, self.criterion, device=self.device)
        except Exception as e:
            print(f"Erro ao calcular Fisher: {e}")

    def update(self, new_data: List[Dict], epochs: int = 3, ewc_penalty: float = 1.0) -> float:
        if not new_data:
            return 0.0

        try:
            X = torch.stack([d["features"] for d in new_data]).float()
            y = torch.stack([d["target"] for d in new_data]).float()
            dataset = TensorDataset(X, y)
            loader = DataLoader(dataset, batch_size=32, shuffle=True)

            optimizer = optim.Adam(self.target_model.parameters(), lr=1e-4)
            self.target_model.train()

            total_loss = 0.0
            for epoch in range(epochs):
                for batch_x, batch_y in loader:
                    batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)

                    optimizer.zero_grad()
                    preds = self.target_model(batch_x)
                    task_loss = self.criterion(preds, batch_y)

                    penalty = self.ewc.ewc_loss(device=self.device) * ewc_penalty
                    loss = task_loss + penalty

                    loss.backward()
                    optimizer.step()
                    total_loss += loss.item()

            return total_loss / (len(loader) * epochs)

        except Exception as e:
            print(f"Erro no update: {e}")
            return -1.0
