from typing import List

import torch
from torchsim.core.graph.inverse_pass_packet import InversePassOutputPacket, InversePassInputPacket
from torchsim.core.graph.slot_container import MemoryBlocks, Inputs
from torchsim.core.graph.unit import InvertibleUnit
from torchsim.core.graph.worker_node_base import InvertibleWorkerNodeBase
from torchsim.core.memory.tensor_creator import TensorCreator


class UnsqueezeNodeUnit(InvertibleUnit):
    def __init__(self, creator: TensorCreator, shape, dim):
        super().__init__(creator.device)
        self.dim = dim
        self.output = creator.zeros(shape, dtype=self._float_dtype, device=creator.device)

    def step(self, input_tensor: torch.Tensor):
        self.output.copy_(input_tensor.unsqueeze(self.dim))

    def inverse_projection(self, output_tensor: torch.Tensor) -> torch.Tensor:
        return output_tensor.squeeze(self.dim)


class UnsqueezeNodeInputs(Inputs):
    def __init__(self, owner):
        super().__init__(owner)
        self.input = self.create("Input")


class UnsqueezeNodeOutputs(MemoryBlocks):
    def __init__(self, owner):
        super().__init__(owner)
        self.output = self.create("Output")

    def prepare_slots(self, unit: UnsqueezeNodeUnit):
        self.output.tensor = unit.output


class UnsqueezeNode(InvertibleWorkerNodeBase[UnsqueezeNodeInputs, UnsqueezeNodeOutputs]):
    """Adds one singular dimension at a desired place of the input tensor."""

    # TODO: add validation

    _unit: UnsqueezeNodeUnit

    inputs: UnsqueezeNodeInputs
    outputs: UnsqueezeNodeOutputs

    def __init__(self, dim, name="Unsqueeze"):
        super().__init__(name=name, inputs=UnsqueezeNodeInputs(self),
                         outputs=UnsqueezeNodeOutputs(self))
        self._dim = dim

    def _create_unit(self, creator: TensorCreator):
        output_dim = self.inputs.input.tensor.shape[:self._dim] + (1,) + self.inputs.input.tensor.shape[self._dim:]
        output_dim = tuple(output_dim)
        return UnsqueezeNodeUnit(creator, output_dim, self._dim)

    def _step(self):
        self._unit.step(self.inputs.input.tensor)

    def _inverse_projection(self, data: InversePassOutputPacket) -> List[InversePassInputPacket]:
        result = self._unit.inverse_projection(data.tensor)

        return [InversePassInputPacket(result, self.inputs.input)]
