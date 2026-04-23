from dataclasses import dataclass, field
from typing import List, Any

@dataclass
class BasicBlock:
    id: int
    instructions: List[Any] = field(default_factory=list)
    successors: List[int] = field(default_factory=list)
    predecessors: List[int] = field(default_factory=list)
    label: str = ""

    def __repr__(self):
        return f"Block[{self.id}]: {len(self.instructions)} instructions"

class BasicBlockBuilder:
    def __init__(self):
        self.blocks: List[BasicBlock] = []
        self.current_block_id = 0

    def new_block(self, label="") -> BasicBlock:
        block = BasicBlock(id=self.current_block_id, label=label)
        self.blocks.append(block)
        self.current_block_id += 1
        return block

    def add_edge(self, from_id: int, to_id: int):
        self.blocks[from_id].successors.append(to_id)
        self.blocks[to_id].predecessors.append(from_id)