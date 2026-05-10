from optimum.onnxruntime import ORTModelForCustomTasks

# Load and export to ONNX
model_id = "bernddoser/IllustrisTNG_SKIRT_SDSS"
vae = ORTModelForCustomTasks.from_pretrained(model_id, subfolder="illustris_vae_resnet18", file_name="decoder.onnx", export=False)

# Save the optimized weights
vae.save_pretrained("./onnx_vae")