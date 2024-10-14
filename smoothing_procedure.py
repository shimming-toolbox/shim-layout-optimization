import slicer
import os
import click

@click.command()
@click.option('-m','--main_volume_path', required=True, help='Path to the main volume')
@click.option('-s','--segmentation_path', required=True, help='Path to the SAMSEG segmentation')
@click.option('-o','--output_path', required=True, help='Path to the output file')
def smoothing_procedure(main_volume_path, segmentation_path, output_path):
    """
    Perform a smoothing procedure on a given volume and segmentation in Slicer.

    This function loads a main volume and its corresponding SAMSEG segmentation, 
    keeps only the skull and eyes labels, applies smoothing and island removal effects 
    on the skull, and then saves the processed segmentation to the specified output path.

    Parameters:
    - main_volume_path (str): Path to the main volume file (subject T1w image).
    - segmentation_path (str): Path to the SAMSEG segmentation file.
    - output_path (str): Path where the output labelmap will be saved.

    Returns:
        None

    Example to run the script in a terminal:
        Slicer.exe --python-script smoothing_procedure.py 
                    -m "C:/path/to/main_volume.nii.gz" 
                    -s "C:/path/to/segmentation.nii.gz" 
                    -o "C:/path/to/output_labelmap.nii.gz"
    
    """

    print("Starting the smoothing procedure...")

    # Load the main volume and segmentation
    main_filename = main_volume_path.split('\\')[-1] # Get the filename from the path

    # Remove the extension to
    main_filename_without_extension = main_filename.split('.')[0]

    print(f"Loading main volume from: {main_volume_path}")
    slicer.util.loadVolume(main_volume_path)
    print("Main volume loaded")
    masterVolumeNode = slicer.util.getNode(main_filename_without_extension)
    print("Main volume node obtained")
    
    print(f"Loading segmentation from: {segmentation_path}")
    segmentation_node = slicer.util.loadSegmentation(segmentation_path)
    print("Segmentation loaded")
    
    # Create segment editor to get access to effects
    segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
    segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
    segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
    segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
    segmentEditorWidget.setSegmentationNode(segmentation_node)
    segmentEditorWidget.setMasterVolumeNode(masterVolumeNode)

    # Define the segment to select
    segmentEditorNode.SetSelectedSegmentID('Segment_165')

    # Islands
    segmentEditorWidget.setActiveEffectByName("Islands")
    effect = segmentEditorWidget.activeEffect()
    effect.setParameter("Operation", "REMOVE_SMALL_ISLANDS")
    effect.self().onApply()

    # Smoothing
    segmentEditorWidget.setActiveEffectByName("Smoothing")
    effect = segmentEditorWidget.activeEffect()
    effect.setParameter("SmoothingMethod", "MORPHOLOGICAL_CLOSING")
    effect.setParameter("KernelSizeMm", 11)
    effect.self().onApply()

    # List of segments to keep
    segmentsToKeep = ['Segment_165', 'Segment_259'] # Skull and eyes

    segmentation = segmentation_node.GetSegmentation()
    # List to store segment IDs that need to be removed
    segmentsToRemove = []

    # Iterate through all segment IDs in the segmentation
    segmentIDs = [segmentation.GetNthSegmentID(i) for i in range(segmentation.GetNumberOfSegments())]

    for segmentID in segmentIDs:
        # Get the segment name
        segmentName = segmentation.GetSegment(segmentID).GetName()
        
        # Check if the segment name is not in the list of segments to keep
        if segmentName not in segmentsToKeep:
            # Add the segment ID to the list of segments to remove
            segmentsToRemove.append(segmentID)

    # Remove segments that are not in the list of segments to keep
    for segmentID in segmentsToRemove:
        segmentation.RemoveSegment(segmentID)

    print("Smoothing procedure completed. Saving the output...")
    # Export segmentation to a labelmap
    labelmapVolumeNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')
    slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(segmentation_node, labelmapVolumeNode, masterVolumeNode)
    slicer.util.saveNode(labelmapVolumeNode, output_path)

if __name__ == '__main__':  
    smoothing_procedure()  

