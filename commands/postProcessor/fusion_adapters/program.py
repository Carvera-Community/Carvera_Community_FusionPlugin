from adsk import cam


class FusionProgramAdapter:
    def machine_has_atc(self, program) -> bool:
        if program.machine is None:
            return False
        tooling = cam.ToolingCapabilitiesMachineElement.cast(
            program.machine.elements.itemById("tooling", "default")
        )
        return tooling is not None and tooling.isToolChangerAutomatic

    def machine_tool_slots(self, program) -> int:
        if not self.machine_has_atc(program):
            return 1
        tooling = cam.ToolingCapabilitiesMachineElement.cast(
            program.machine.elements.itemById("tooling", "default")
        )
        return tooling.maxToolCount

    def machine_has_a_axis(self, program) -> bool:
        if program.machine is None:
            return False

        controller = cam.ControllerConfigurationMachineElement.cast(
            program.machine.elements.defaultItemByType("controller")
        )
        axes = controller.axisConfigurations
        unreadableExtraAxis = False
        for index in range(axes.count):
            try:
                axis = axes.item(index)
            except RuntimeError as error:
                if index >= 3 and "axisDefinition" in str(error):
                    unreadableExtraAxis = True
                    continue
                raise

            if cam.RotaryMachineAxisConfiguration.cast(axis) is not None:
                return True

        return unreadableExtraAxis

    def post_process(self, program) -> bool:
        return program.postProcess(cam.NCProgramPostProcessOptions.create())
